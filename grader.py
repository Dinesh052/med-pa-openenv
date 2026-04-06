"""
Grading logic for the Medical Prior Authorization environment.

Deterministic graders that score agent performance 0.0-1.0 based on:
  - Decision correctness (weight varies by difficulty)
  - Rationale quality — strict: must cite guideline ID AND key findings
  - Correct info gathering — must look up guideline; request correct missing docs
  - Process quality — proper investigation steps before deciding
  - Penalties for hallucinated guidelines, repeated actions, skipping investigation
"""

import re
from typing import Any, Dict, List, Optional


def _normalize(val: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, val))


def _check_rationale_references(
    rationale: Optional[str], key_findings: List[str], guideline_id: str
) -> float:
    """Score rationale quality — STRICT matching.

    Requires:
      - Exact guideline ID match — 0.4 of rationale score
      - Each key finding must have at least 2 matching keywords (4+ chars) — 0.6 of score
    """
    if not rationale or len(rationale.strip()) < 20:
        return 0.0

    rationale_lower = rationale.lower()
    score = 0.0

    if guideline_id.lower() in rationale_lower:
        score += 0.4

    findings_found = 0
    for finding in key_findings:
        keywords = [w for w in finding.lower().split() if len(w) >= 4]
        matches = sum(1 for kw in keywords if kw in rationale_lower)
        if matches >= 2:
            findings_found += 1

    if key_findings:
        score += 0.6 * (findings_found / len(key_findings))

    return _normalize(score)


def _extract_actions(actions_taken: List[Dict[str, Any]]):
    """Common action extraction logic."""
    terminal_action = None
    guideline_looked_up = False
    patient_history_checked = False
    formulary_checked = False
    info_requested = False
    requested_fields: List[str] = []
    repeated_actions = 0
    seen_actions: List[str] = []
    action_sequence: List[str] = []
    actions_before_decision = 0

    for act in actions_taken:
        act_type = act.get("action_type", "")
        act_key = f"{act_type}:{act.get('payload', {})}"

        if act_key in seen_actions:
            repeated_actions += 1
        seen_actions.append(act_key)
        action_sequence.append(act_type)

        if act_type == "lookup_guideline":
            guideline_looked_up = True
        if act_type == "get_patient_history":
            patient_history_checked = True
        if act_type == "check_formulary":
            formulary_checked = True
        if act_type == "request_info":
            info_requested = True
            requested_fields.extend(act.get("payload", {}).get("fields", []))
        if act_type in ("approve", "deny", "request_info"):
            terminal_action = act
            break
        actions_before_decision += 1

    return {
        "terminal_action": terminal_action,
        "guideline_looked_up": guideline_looked_up,
        "patient_history_checked": patient_history_checked,
        "formulary_checked": formulary_checked,
        "info_requested": info_requested,
        "requested_fields": requested_fields,
        "repeated_actions": repeated_actions,
        "action_sequence": action_sequence,
        "actions_before_decision": actions_before_decision,
    }


def _apply_repeat_penalty(breakdown: Dict[str, float], repeated: int, feedback: List[str]):
    if repeated > 0:
        penalty = min(0.2, repeated * 0.1)
        breakdown["penalties"] -= penalty
        feedback.append(f"Penalty: {repeated} repeated action(s) (-{penalty:.2f}).")


def _apply_hallucination_penalty(
    breakdown: Dict[str, float], rationale: str, correct_guidelines: List[str], feedback: List[str]
):
    rationale_upper = (rationale or "").upper()
    gl_refs = re.findall(r"GL-[A-Z0-9]+-\d+", rationale_upper)
    correct_set = {g.upper() for g in correct_guidelines}
    for ref in gl_refs:
        if ref not in correct_set:
            breakdown["penalties"] -= 0.3
            feedback.append(f"Penalty: cited wrong guideline {ref} (-0.30).")
            break


# ── EASY GRADERS ──────────────────────────────────────────


def _grade_easy_approve(
    actions_taken: List[Dict[str, Any]],
    ground_truth: Dict[str, Any],
    max_steps: int,
    guideline_id: str,
    key_findings: List[str],
) -> Dict[str, Any]:
    """Generic easy-approve grader. Decision 0.4, Rationale 0.25, Info 0.2, Process 0.15."""
    breakdown = {
        "decision_correctness": 0.0,
        "rationale_quality": 0.0,
        "info_gathering": 0.0,
        "process_quality": 0.0,
        "penalties": 0.0,
    }
    feedback: List[str] = []
    ctx = _extract_actions(actions_taken)
    ta = ctx["terminal_action"]

    if ta is None:
        feedback.append("No terminal decision was made.")
        return {"score": 0.0, "breakdown": breakdown, "feedback": " ".join(feedback)}

    # Decision correctness (0.4)
    expected = ground_truth.get("decision", "approve")
    if ta["action_type"] == expected:
        breakdown["decision_correctness"] = 0.4
        feedback.append(f"Correct decision: {expected}.")
    else:
        feedback.append(f"Wrong decision: {ta['action_type']} instead of {expected}.")

    # Rationale quality (0.25)
    rationale = ta.get("rationale", "")
    r_score = _check_rationale_references(rationale, key_findings, guideline_id)
    breakdown["rationale_quality"] = round(0.25 * r_score, 4)
    if r_score >= 0.7:
        feedback.append("Strong rationale with guideline ID and key findings.")
    elif r_score >= 0.3:
        feedback.append("Rationale partially references relevant criteria.")
    else:
        feedback.append("Rationale missing guideline ID or key clinical findings.")

    # Info gathering (0.2)
    if ctx["guideline_looked_up"]:
        breakdown["info_gathering"] = 0.2
        feedback.append("Guideline was consulted before decision.")
    else:
        feedback.append("CRITICAL: Guideline was not consulted — decision made without evidence basis.")

    # Process quality (0.15)
    if ctx["actions_before_decision"] >= 1 and ctx["guideline_looked_up"]:
        if ctx["patient_history_checked"]:
            breakdown["process_quality"] = 0.15
            feedback.append("Thorough investigation: guideline + patient history reviewed.")
        else:
            breakdown["process_quality"] = 0.1
            feedback.append("Adequate investigation: guideline reviewed.")
    elif ctx["actions_before_decision"] >= 1:
        breakdown["process_quality"] = 0.05
        feedback.append("Some investigation performed but guideline not consulted.")
    else:
        feedback.append("No investigation before decision — jumped straight to conclusion.")

    # Penalties
    _apply_repeat_penalty(breakdown, ctx["repeated_actions"], feedback)
    _apply_hallucination_penalty(
        breakdown, ta.get("rationale", ""), ground_truth.get("required_criteria", [guideline_id]), feedback
    )

    total = _normalize(sum(breakdown.values()))
    return {
        "score": round(total, 4),
        "breakdown": {k: round(v, 4) for k, v in breakdown.items()},
        "feedback": " ".join(feedback),
    }


def grade_easy_knee_mri(actions_taken, ground_truth, max_steps=8):
    return _grade_easy_approve(
        actions_taken, ground_truth, max_steps,
        guideline_id="GL-KNEE-MRI-001",
        key_findings=[
            "positive Lachman test with no firm endpoint",
            "physical therapy six weeks completed",
            "functional instability and giving-way episodes",
        ],
    )


def grade_easy_chest_xray(actions_taken, ground_truth, max_steps=8):
    return _grade_easy_approve(
        actions_taken, ground_truth, max_steps,
        guideline_id="GL-CHEST-XRAY-001",
        key_findings=[
            "persistent cough five weeks duration",
            "failed empiric treatment antibiotics and inhaled corticosteroids",
            "diminished breath sounds right base",
        ],
    )


def grade_easy_pt_eval(actions_taken, ground_truth, max_steps=8):
    return _grade_easy_approve(
        actions_taken, ground_truth, max_steps,
        guideline_id="GL-PT-EVAL-001",
        key_findings=[
            "partial-thickness tear supraspinatus tendon MRI confirmed",
            "difficulty overhead activities dressing sleep disruption",
            "positive Neer and Hawkins impingement signs",
        ],
    )


# ── MEDIUM GRADERS ────────────────────────────────────────


def _grade_medium_request_info(
    actions_taken: List[Dict[str, Any]],
    ground_truth: Dict[str, Any],
    max_steps: int,
    guideline_id: str,
    key_findings: List[str],
    post_info_decision: str = "approve",
) -> Dict[str, Any]:
    """Generic medium grader for request_info tasks.
    Decision 0.3, Info request 0.3, Rationale 0.2, Process 0.2.
    """
    breakdown = {
        "decision_correctness": 0.0,
        "info_request_quality": 0.0,
        "rationale_quality": 0.0,
        "process_quality": 0.0,
        "penalties": 0.0,
    }
    feedback: List[str] = []
    ctx = _extract_actions(actions_taken)
    ta = ctx["terminal_action"]

    required_missing = set(ground_truth.get("required_missing_fields", []))

    # Info request quality (0.3)
    if ctx["info_requested"]:
        requested_set = set(ctx["requested_fields"])
        correct_fields = required_missing & requested_set
        wrong_fields = requested_set - required_missing

        if required_missing:
            field_ratio = len(correct_fields) / len(required_missing)
            breakdown["info_request_quality"] = round(0.1 + 0.2 * field_ratio, 4)
            feedback.append(f"Requested {len(correct_fields)}/{len(required_missing)} correct missing fields.")
        else:
            breakdown["info_request_quality"] = 0.1

        if wrong_fields:
            penalty = min(0.1, len(wrong_fields) * 0.03)
            breakdown["info_request_quality"] -= penalty
            feedback.append(f"Requested {len(wrong_fields)} unnecessary field(s) (-{penalty:.2f}).")
    else:
        feedback.append("CRITICAL: Did not request additional information — missing documentation.")

    # Decision correctness (0.3)
    if ta is None:
        feedback.append("No terminal decision was made.")
    elif ta["action_type"] == "request_info":
        breakdown["decision_correctness"] = 0.3
        feedback.append("Correct decision: requested additional information.")
    elif ctx["info_requested"] and ta["action_type"] == post_info_decision:
        breakdown["decision_correctness"] = 0.3
        feedback.append("Correct final decision after receiving requested information.")
    elif not ctx["info_requested"] and ta["action_type"] == post_info_decision:
        breakdown["decision_correctness"] = 0.1
        feedback.append("Correct decision but critically skipped requesting missing documentation.")
    elif not ctx["info_requested"] and ta["action_type"] == "deny":
        feedback.append("Incorrectly denied without requesting missing documentation.")
    else:
        feedback.append(f"Wrong decision: {ta['action_type']}. Expected: request_info.")

    # Rationale quality (0.2)
    if ta:
        rationale = ta.get("rationale", "")
        r_score = _check_rationale_references(rationale, key_findings, guideline_id)
        breakdown["rationale_quality"] = round(0.2 * r_score, 4)
        if r_score >= 0.5:
            feedback.append("Rationale adequately references guideline and findings.")
        else:
            feedback.append(f"Rationale weak — must cite {guideline_id} and specific findings.")

    # Process quality (0.2)
    process_score = 0.0
    if ctx["guideline_looked_up"]:
        process_score += 0.08
        feedback.append("Guideline consulted.")
    else:
        feedback.append("Guideline not consulted before decision.")

    if ctx["info_requested"] and ctx["guideline_looked_up"]:
        try:
            gl_idx = ctx["action_sequence"].index("lookup_guideline")
            ri_idx = ctx["action_sequence"].index("request_info")
            if gl_idx < ri_idx:
                process_score += 0.07
                feedback.append("Correct workflow: guideline → request info → decide.")
            else:
                process_score += 0.03
                feedback.append("Workflow issue: requested info before looking up guideline.")
        except ValueError:
            process_score += 0.03

    if ctx["formulary_checked"]:
        process_score += 0.05
        feedback.append("Formulary checked (bonus).")

    breakdown["process_quality"] = round(min(0.2, process_score), 4)

    # Penalties
    _apply_repeat_penalty(breakdown, ctx["repeated_actions"], feedback)

    total = _normalize(sum(breakdown.values()))
    return {
        "score": round(total, 4),
        "breakdown": {k: round(v, 4) for k, v in breakdown.items()},
        "feedback": " ".join(feedback),
    }


def grade_medium_humira(actions_taken, ground_truth, max_steps=8):
    return _grade_medium_request_info(
        actions_taken, ground_truth, max_steps,
        guideline_id="GL-BIOLOGIC-001",
        key_findings=[
            "CDAI score 285 moderate-to-severe disease activity",
            "mesalamine failed inadequate response",
            "prednisone taper dependent symptoms flare",
            "step therapy immunomodulators not documented",
        ],
        post_info_decision="approve",
    )


def grade_medium_ozempic(actions_taken, ground_truth, max_steps=8):
    return _grade_medium_request_info(
        actions_taken, ground_truth, max_steps,
        guideline_id="GL-GLP1-001",
        key_findings=[
            "HbA1c 8.4% despite lifestyle modifications",
            "metformin discontinued severe GI intolerance",
            "BMI 36.2 morbid obesity with comorbidity",
            "lifestyle modification records incomplete",
        ],
        post_info_decision="approve",
    )


def grade_medium_sleep_study(actions_taken, ground_truth, max_steps=8):
    """Medium-approve: must recognize failed home test + comorbidities justify in-lab PSG."""
    return _grade_easy_approve(
        actions_taken, ground_truth, max_steps,
        guideline_id="GL-SLEEP-001",
        key_findings=[
            "Epworth Sleepiness Scale score 15",
            "home sleep test technically inadequate failed",
            "atrial fibrillation and moderate COPD complex comorbidities",
            "witnessed apneic episodes snoring",
        ],
    )


# ── HARD GRADERS ──────────────────────────────────────────


def _grade_hard_deny(
    actions_taken: List[Dict[str, Any]],
    ground_truth: Dict[str, Any],
    max_steps: int,
    primary_guideline: str,
    all_guidelines: List[str],
    key_findings: List[str],
    contraindication_signals: List[List[str]],
    correct_denial_code: str,
    alt_denial_codes: List[str],
) -> Dict[str, Any]:
    """Generic hard-deny grader.
    Contraindication 0.25, Guideline conflict 0.15, Denial code 0.15,
    Decision 0.15, Rationale 0.15, Process 0.15.
    """
    breakdown = {
        "contraindication_found": 0.0,
        "guideline_conflict_resolved": 0.0,
        "denial_code_quality": 0.0,
        "decision_correctness": 0.0,
        "rationale_quality": 0.0,
        "process_quality": 0.0,
        "penalties": 0.0,
    }
    feedback: List[str] = []
    ctx = _extract_actions(actions_taken)
    ta = ctx["terminal_action"]

    if ta is None:
        feedback.append("No terminal decision was made.")
        return {"score": 0.0, "breakdown": breakdown, "feedback": " ".join(feedback)}

    # Decision correctness (0.15)
    if ta["action_type"] == "deny":
        breakdown["decision_correctness"] = 0.15
        feedback.append("Correct decision: denied.")
    else:
        feedback.append(f"CRITICAL: Wrong decision: {ta['action_type']}. Should have denied — active contraindication.")
        breakdown["penalties"] -= 0.1
        feedback.append("Major penalty: approving a patient with active contraindication (-0.10).")

    # Contraindication found (0.25) — check signal groups
    rationale = (ta.get("rationale") or "").lower()
    all_text = " ".join(
        (a.get("rationale") or "") + " " + str(a.get("payload", {})) for a in actions_taken
    ).lower()
    combined = rationale + " " + all_text

    signals_hit = 0
    for group in contraindication_signals:
        if any(s in combined for s in group):
            signals_hit += 1

    total_groups = len(contraindication_signals)
    if signals_hit == total_groups:
        breakdown["contraindication_found"] = 0.25
        feedback.append("Correctly identified all contraindication elements.")
    elif signals_hit >= total_groups - 1:
        breakdown["contraindication_found"] = 0.15
        feedback.append("Partially identified contraindication — missing some specifics.")
    elif signals_hit >= 1:
        breakdown["contraindication_found"] = 0.08
        feedback.append("Vaguely referenced contraindication but lacked specifics.")
    else:
        feedback.append("FAILED to identify the key contraindication.")

    # Guideline conflict resolution (0.15)
    primary_lower = primary_guideline.lower()
    other_gls = [g.lower() for g in all_guidelines if g != primary_guideline]
    mentions_primary = primary_lower in combined
    mentions_others = any(g in combined for g in other_gls)

    if mentions_primary:
        if mentions_others:
            if primary_lower in rationale:
                breakdown["guideline_conflict_resolved"] = 0.15
                feedback.append(f"Identified guidelines and correctly applied {primary_guideline}.")
            else:
                breakdown["guideline_conflict_resolved"] = 0.08
                feedback.append("Referenced multiple guidelines but unclear which was applied.")
        else:
            breakdown["guideline_conflict_resolved"] = 0.15
            feedback.append(f"Correctly identified {primary_guideline} as applicable.")
    elif mentions_others:
        breakdown["guideline_conflict_resolved"] = 0.03
        feedback.append("Applied secondary guideline instead of primary.")
    else:
        feedback.append("Did not reference any specific guideline for the denial.")

    # Denial code quality (0.15)
    denial_payload = ta.get("payload", {})
    agent_code = (
        denial_payload.get("reason_code", "")
        or denial_payload.get("denial_code", "")
        or denial_payload.get("denial_reason", "")
    ).upper()

    if agent_code == correct_denial_code:
        breakdown["denial_code_quality"] = 0.15
        feedback.append(f"Correct denial reason code: {correct_denial_code}.")
    elif agent_code in [c.upper() for c in alt_denial_codes]:
        breakdown["denial_code_quality"] = 0.07
        feedback.append(f"Acceptable but suboptimal denial code: {agent_code}.")
    elif ta["action_type"] == "deny" and agent_code:
        breakdown["denial_code_quality"] = 0.03
        feedback.append(f"Denial code '{agent_code}' is not the best fit for this case.")
    elif ta["action_type"] == "deny":
        feedback.append("Denied but provided no reason code.")

    # Rationale quality (0.15)
    r_score = _check_rationale_references(ta.get("rationale"), key_findings, primary_guideline)
    breakdown["rationale_quality"] = round(0.15 * r_score, 4)
    if r_score >= 0.6:
        feedback.append("Strong rationale addressing guideline criteria and contraindication.")
    elif r_score >= 0.3:
        feedback.append("Rationale partially addresses the case complexity.")
    else:
        feedback.append("Rationale insufficient — must address guideline and contraindication.")

    # Process quality (0.15)
    process_score = 0.0
    if ctx["guideline_looked_up"]:
        process_score += 0.06
    else:
        feedback.append("Guideline not consulted on a complex case — major process gap.")
    if ctx["patient_history_checked"]:
        process_score += 0.06
    else:
        feedback.append("Patient history not reviewed on a case with relevant history.")
    investigation_steps = sum(
        1 for a in ctx["action_sequence"]
        if a in ("lookup_guideline", "get_patient_history", "check_formulary", "request_info")
    )
    if investigation_steps >= 2:
        process_score += 0.03
    breakdown["process_quality"] = round(min(0.15, process_score), 4)

    # Penalties
    _apply_repeat_penalty(breakdown, ctx["repeated_actions"], feedback)
    if ta["action_type"] == "approve":
        _apply_hallucination_penalty(breakdown, ta.get("rationale", ""), all_guidelines, feedback)

    total = _normalize(sum(breakdown.values()))
    return {
        "score": round(total, 4),
        "breakdown": {k: round(v, 4) for k, v in breakdown.items()},
        "feedback": " ".join(feedback),
    }


def grade_hard_spinal_fusion(actions_taken, ground_truth, max_steps=8):
    return _grade_hard_deny(
        actions_taken, ground_truth, max_steps,
        primary_guideline="GL-SPINE-FUSION-001",
        all_guidelines=["GL-SPINE-FUSION-001", "GL-SPINE-FUSION-002"],
        key_findings=[
            "MRSA wound infection completed vancomycin two weeks ago",
            "wound cultures pending final clearance",
            "BMI 38 exceeds threshold for elective surgery",
            "no active infection criteria not met",
        ],
        contraindication_signals=[
            ["mrsa", "infection", "wound infection"],
            ["cultures pending", "clearance", "not cleared"],
            ["contraindication", "contraindicated", "active infection"],
        ],
        correct_denial_code="CONTRAINDICATION_ACTIVE_INFECTION",
        alt_denial_codes=["ACTIVE_INFECTION", "CONTRAINDICATION_INFECTION", "MEDICAL_CONTRAINDICATION"],
    )


def grade_hard_cardiac_cath(actions_taken, ground_truth, max_steps=8):
    return _grade_hard_deny(
        actions_taken, ground_truth, max_steps,
        primary_guideline="GL-CARDIAC-CATH-001",
        all_guidelines=["GL-CARDIAC-CATH-001", "GL-CARDIAC-CATH-002"],
        key_findings=[
            "eGFR 22 stage 4 CKD below threshold of 30",
            "GI bleed duodenal ulcer two weeks ago transfusion required",
            "hemoglobin 9.2 active bleeding risk",
            "contrast nephropathy risk with eGFR 22",
        ],
        contraindication_signals=[
            ["egfr 22", "egfr", "renal", "ckd", "stage 4"],
            ["gi bleed", "gastrointestinal bleed", "duodenal ulcer", "active bleeding"],
            ["hemoglobin 9.2", "anemia", "transfusion"],
            ["contraindication", "contraindicated"],
        ],
        correct_denial_code="CONTRAINDICATION_ACTIVE_BLEEDING_AND_RENAL",
        alt_denial_codes=[
            "CONTRAINDICATION_RENAL", "CONTRAINDICATION_BLEEDING",
            "ACTIVE_BLEEDING", "RENAL_INSUFFICIENCY", "MEDICAL_CONTRAINDICATION",
        ],
    )


def grade_hard_gene_therapy(actions_taken, ground_truth, max_steps=8):
    return _grade_hard_deny(
        actions_taken, ground_truth, max_steps,
        primary_guideline="GL-GENE-THERAPY-001",
        all_guidelines=["GL-GENE-THERAPY-001"],
        key_findings=[
            "ALT 85 elevated above normal 45",
            "AST 72 elevated transaminases",
            "no active hepatic disease criteria not met",
            "hepatotoxicity risk with Zolgensma gene therapy",
        ],
        contraindication_signals=[
            ["alt 85", "alt", "transaminase", "elevated"],
            ["ast 72", "ast", "hepatic"],
            ["liver", "hepatotoxicity", "hepatic disease", "hepatic concern"],
            ["contraindication", "contraindicated"],
        ],
        correct_denial_code="CONTRAINDICATION_HEPATIC_DISEASE",
        alt_denial_codes=[
            "HEPATIC_CONTRAINDICATION", "ELEVATED_TRANSAMINASES",
            "ACTIVE_HEPATIC_DISEASE", "MEDICAL_CONTRAINDICATION",
        ],
    )


# ── DISPATCHER ────────────────────────────────────────────

GRADERS = {
    "easy_knee_mri": grade_easy_knee_mri,
    "easy_chest_xray": grade_easy_chest_xray,
    "easy_pt_eval": grade_easy_pt_eval,
    "medium_humira": grade_medium_humira,
    "medium_ozempic": grade_medium_ozempic,
    "medium_sleep_study": grade_medium_sleep_study,
    "hard_spinal_fusion": grade_hard_spinal_fusion,
    "hard_cardiac_cath": grade_hard_cardiac_cath,
    "hard_gene_therapy": grade_hard_gene_therapy,
}


def grade_task(
    task_id: str,
    actions_taken: List[Dict[str, Any]],
    ground_truth: Dict[str, Any],
    max_steps: int = 8,
) -> Dict[str, Any]:
    """Grade a task given the actions taken and ground truth."""
    if task_id not in GRADERS:
        raise ValueError(f"Unknown task_id: {task_id}. Available: {list(GRADERS.keys())}")
    return GRADERS[task_id](actions_taken, ground_truth, max_steps)
