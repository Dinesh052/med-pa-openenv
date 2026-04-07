"""
Grading logic for the Medical Prior Authorization environment.

Deterministic graders that score agent performance 0.0–1.0 based on:
  - Decision correctness (0.4)
  - Rationale quality (0.25) — strict: must cite guideline ID AND multiple key findings
  - Correct info gathering (0.2) — must look up guideline; request correct missing docs
  - Process quality (0.15) — proper investigation steps before deciding
  - Penalties for hallucinated guidelines, repeated actions, skipping investigation
"""

import re
from typing import Any, Dict, List, Optional, Tuple


def _normalize(val: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value and ensure score is strictly within (0, 1) — never exactly 0.0 or 1.0."""
    clamped = max(lo, min(hi, val))
    # Validator requires 0 < score < 1 (strict inequality)
    if clamped <= 0.0:
        return 0.01
    if clamped >= 1.0:
        return 0.99
    return clamped


def _check_rationale_references(
    rationale: Optional[str], key_findings: List[str], guideline_id: str
) -> float:
    """Score rationale quality — STRICT matching.

    Requires:
      - Exact guideline ID match (e.g. "GL-ORTHO-001") — 0.4 of rationale score
      - Each key finding must have at least 2 matching keywords (4+ chars) — 0.6 of score
    """
    if not rationale or len(rationale.strip()) < 20:
        return 0.0

    rationale_lower = rationale.lower()
    score = 0.0

    # Exact guideline ID match (strict — must have the ID)
    if guideline_id.lower() in rationale_lower:
        score += 0.4

    # Key findings — require at least 2 keyword matches per finding
    findings_found = 0
    for finding in key_findings:
        keywords = [w for w in finding.lower().split() if len(w) >= 4]
        matches = sum(1 for kw in keywords if kw in rationale_lower)
        if matches >= 2:
            findings_found += 1

    if key_findings:
        findings_ratio = findings_found / len(key_findings)
        score += 0.6 * findings_ratio

    return _normalize(score)


def grade_easy(
    actions_taken: List[Dict[str, Any]],
    ground_truth: Dict[str, Any],
    max_steps: int = 8,
) -> Dict[str, Any]:
    """Grade the easy task (Knee MRI approval).

    Scoring (stricter):
      - Decision correctness: 0.4 (must approve)
      - Rationale quality: 0.25 (must cite GL-ORTHO-001 + key findings specifically)
      - Info gathering: 0.2 (MUST look up guideline — 0.0 if skipped)
      - Process quality: 0.15 (proper investigation before deciding)
    """
    breakdown: Dict[str, float] = {
        "decision_correctness": 0.0,
        "rationale_quality": 0.0,
        "info_gathering": 0.0,
        "process_quality": 0.0,
        "penalties": 0.0,
    }
    feedback_parts: List[str] = []

    terminal_action = None
    guideline_looked_up = False
    patient_history_checked = False
    repeated_actions = 0
    seen_actions: List[str] = []
    actions_before_decision = 0

    for act in actions_taken:
        act_type = act.get("action_type", "")
        act_key = f"{act_type}:{act.get('payload', {})}"

        if act_key in seen_actions:
            repeated_actions += 1
        seen_actions.append(act_key)

        if act_type == "lookup_guideline":
            guideline_looked_up = True
        if act_type == "get_patient_history":
            patient_history_checked = True
        if act_type in ("approve", "deny"):
            terminal_action = act
            break
        actions_before_decision += 1

    if terminal_action is None:
        feedback_parts.append("No terminal decision (approve/deny) was made.")
        return {
            "score": 0.01,
            "breakdown": breakdown,
            "feedback": " ".join(feedback_parts),
        }

    # Decision correctness (0.4)
    if terminal_action["action_type"] == ground_truth["correct_decision"]:
        breakdown["decision_correctness"] = 0.4
        feedback_parts.append("Correct decision: approved.")
    else:
        feedback_parts.append(
            f"Wrong decision: {terminal_action['action_type']} instead of {ground_truth['correct_decision']}."
        )

    # Rationale quality (0.25) — strict
    rationale = terminal_action.get("rationale", "")
    rationale_score = _check_rationale_references(
        rationale,
        ground_truth["key_findings"],
        ground_truth["applicable_guideline"],
    )
    breakdown["rationale_quality"] = round(0.25 * rationale_score, 4)
    if rationale_score >= 0.7:
        feedback_parts.append("Strong rationale with guideline ID and key findings.")
    elif rationale_score >= 0.3:
        feedback_parts.append("Rationale partially references relevant criteria.")
    else:
        feedback_parts.append("Rationale missing guideline ID or key clinical findings.")

    # Info gathering (0.2) — MUST look up guideline, no free points
    if guideline_looked_up:
        breakdown["info_gathering"] = 0.2
        feedback_parts.append("Guideline was consulted before decision.")
    else:
        breakdown["info_gathering"] = 0.0
        feedback_parts.append("CRITICAL: Guideline was not consulted — decision made without evidence basis.")

    # Process quality (0.15) — did agent investigate before deciding?
    if actions_before_decision >= 1 and guideline_looked_up:
        breakdown["process_quality"] = 0.1
        if patient_history_checked:
            breakdown["process_quality"] = 0.15
            feedback_parts.append("Thorough investigation: guideline + patient history reviewed.")
        else:
            feedback_parts.append("Adequate investigation: guideline reviewed.")
    elif actions_before_decision >= 1:
        breakdown["process_quality"] = 0.05
        feedback_parts.append("Some investigation performed but guideline not consulted.")
    else:
        breakdown["process_quality"] = 0.0
        feedback_parts.append("No investigation before decision — jumped straight to conclusion.")

    # Penalties
    if repeated_actions > 0:
        penalty = min(0.2, repeated_actions * 0.1)
        breakdown["penalties"] = -penalty
        feedback_parts.append(f"Penalty: {repeated_actions} repeated action(s) (-{penalty:.2f}).")

    # Hallucinated guideline penalty — check for any GL- reference that isn't the correct one
    rationale_str = (terminal_action.get("rationale", "") or "").upper()
    gl_refs = re.findall(r"GL-[A-Z]+-\d+", rationale_str)
    correct_gl = ground_truth["applicable_guideline"].upper()
    for ref in gl_refs:
        if ref != correct_gl:
            breakdown["penalties"] -= 0.3
            feedback_parts.append(f"Penalty: cited wrong guideline {ref} (-0.30).")
            break

    total = sum(breakdown.values())
    total = _normalize(total)

    return {
        "score": round(total, 4),
        "breakdown": {k: round(v, 4) for k, v in breakdown.items()},
        "feedback": " ".join(feedback_parts),
    }


def grade_medium(
    actions_taken: List[Dict[str, Any]],
    ground_truth: Dict[str, Any],
    max_steps: int = 8,
) -> Dict[str, Any]:
    """Grade the medium task (Humira for Crohn's).

    Scoring (stricter):
      - Decision correctness: 0.3 (correct final decision AFTER info received)
      - Info request quality: 0.3 (must request info + correct fields)
      - Rationale quality: 0.2 (must cite GL-GI-002 + specific findings)
      - Process quality: 0.2 (must: lookup guideline -> request info -> decide)
    """
    breakdown: Dict[str, float] = {
        "decision_correctness": 0.0,
        "info_request_quality": 0.0,
        "rationale_quality": 0.0,
        "process_quality": 0.0,
        "penalties": 0.0,
    }
    feedback_parts: List[str] = []

    terminal_action = None
    info_requested = False
    requested_fields: List[str] = []
    guideline_looked_up = False
    formulary_checked = False
    repeated_actions = 0
    seen_actions: List[str] = []
    action_sequence: List[str] = []

    for act in actions_taken:
        act_type = act.get("action_type", "")
        act_key = f"{act_type}:{act.get('payload', {})}"

        if act_key in seen_actions:
            repeated_actions += 1
        seen_actions.append(act_key)
        action_sequence.append(act_type)

        if act_type == "lookup_guideline":
            guideline_looked_up = True
        if act_type == "check_formulary":
            formulary_checked = True
        if act_type == "request_info":
            info_requested = True
            requested_fields.extend(act.get("payload", {}).get("fields", []))
        if act_type in ("approve", "deny"):
            terminal_action = act
            break

    # Info request quality (0.3) — core of this task
    required_missing = set(ground_truth["missing_fields"])
    if info_requested:
        requested_set = set(requested_fields)
        correct_fields = required_missing & requested_set
        wrong_fields = requested_set - required_missing

        if required_missing:
            field_ratio = len(correct_fields) / len(required_missing)
            # 0.1 for requesting at all + up to 0.2 for correct fields
            breakdown["info_request_quality"] = round(0.1 + 0.2 * field_ratio, 4)
            feedback_parts.append(
                f"Requested {len(correct_fields)}/{len(required_missing)} correct missing fields."
            )
        else:
            breakdown["info_request_quality"] = 0.1

        # Penalty for wrong fields
        if wrong_fields:
            penalty = min(0.1, len(wrong_fields) * 0.03)
            breakdown["info_request_quality"] -= penalty
            feedback_parts.append(f"Requested {len(wrong_fields)} unnecessary field(s) (-{penalty:.2f}).")
    else:
        breakdown["info_request_quality"] = 0.0
        feedback_parts.append("CRITICAL: Did not request additional information — missing step therapy docs.")

    # Decision correctness (0.3)
    if terminal_action is None:
        feedback_parts.append("No terminal decision was made.")
    else:
        post_info_decision = ground_truth.get("post_info_decision", "approve")

        if info_requested and terminal_action["action_type"] == post_info_decision:
            # Best case: requested info, then correct decision
            breakdown["decision_correctness"] = 0.3
            feedback_parts.append("Correct final decision after receiving requested information.")
        elif not info_requested and terminal_action["action_type"] == post_info_decision:
            # Skipped info request but got right decision — partial credit only
            breakdown["decision_correctness"] = 0.1
            feedback_parts.append("Correct decision but critically skipped requesting missing documentation.")
        elif not info_requested and terminal_action["action_type"] == "deny":
            # Denied without checking — wrong
            breakdown["decision_correctness"] = 0.0
            feedback_parts.append("Incorrectly denied without requesting missing step therapy documentation.")
        else:
            feedback_parts.append(
                f"Wrong decision: {terminal_action['action_type']}. Expected: request info -> {post_info_decision}."
            )

    # Rationale quality (0.2) — strict
    if terminal_action:
        rationale = terminal_action.get("rationale", "")
        rationale_score = _check_rationale_references(
            rationale,
            ground_truth["key_findings"],
            ground_truth["applicable_guideline"],
        )
        breakdown["rationale_quality"] = round(0.2 * rationale_score, 4)
        if rationale_score >= 0.5:
            feedback_parts.append("Rationale adequately references guideline and findings.")
        else:
            feedback_parts.append("Rationale weak — must cite GL-GI-002 and specific therapy failures.")

    # Process quality (0.2) — must follow proper workflow
    process_score = 0.0
    if guideline_looked_up:
        process_score += 0.08
        feedback_parts.append("Guideline consulted.")
    else:
        feedback_parts.append("Guideline not consulted before decision.")

    if info_requested and guideline_looked_up:
        # Check ordering: guideline should come before request_info
        try:
            gl_idx = action_sequence.index("lookup_guideline")
            ri_idx = action_sequence.index("request_info")
            if gl_idx < ri_idx:
                process_score += 0.07
                feedback_parts.append("Correct workflow: guideline -> request info -> decide.")
            else:
                process_score += 0.03
                feedback_parts.append("Workflow issue: requested info before looking up guideline.")
        except ValueError:
            process_score += 0.03

    if formulary_checked:
        process_score += 0.05
        feedback_parts.append("Formulary checked (bonus).")

    breakdown["process_quality"] = round(min(0.2, process_score), 4)

    # Penalties
    if repeated_actions > 0:
        penalty = min(0.2, repeated_actions * 0.1)
        breakdown["penalties"] = -penalty
        feedback_parts.append(f"Penalty: {repeated_actions} repeated action(s) (-{penalty:.2f}).")

    total = sum(breakdown.values())
    total = _normalize(total)

    return {
        "score": round(total, 4),
        "breakdown": {k: round(v, 4) for k, v in breakdown.items()},
        "feedback": " ".join(feedback_parts),
    }


def grade_hard(
    actions_taken: List[Dict[str, Any]],
    ground_truth: Dict[str, Any],
    max_steps: int = 8,
) -> Dict[str, Any]:
    """Grade the hard task (Spinal Fusion complex denial).

    Scoring (strict — designed so frontier models get 0.3–0.6):
      - Found contraindication (0.25): Must reference BOTH HbA1c value AND threshold
      - Guideline conflict resolution (0.15): Must identify GL-SPINE-003 as applicable
      - Correct denial code (0.15): CONTRAINDICATION_ACTIVE exact; alternatives partial
      - Decision correctness (0.15): deny
      - Rationale quality (0.15): must cite guideline, contraindication, and why
      - Process quality (0.15): must lookup guideline + check history + then decide
    """
    breakdown: Dict[str, float] = {
        "contraindication_found": 0.0,
        "guideline_conflict_resolved": 0.0,
        "denial_code_quality": 0.0,
        "decision_correctness": 0.0,
        "rationale_quality": 0.0,
        "process_quality": 0.0,
        "penalties": 0.0,
    }
    feedback_parts: List[str] = []

    terminal_action = None
    guideline_looked_up = False
    patient_history_checked = False
    repeated_actions = 0
    seen_actions: List[str] = []
    action_sequence: List[str] = []

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
        if act_type in ("approve", "deny"):
            terminal_action = act
            break

    if terminal_action is None:
        feedback_parts.append("No terminal decision was made.")
        return {
            "score": 0.01,
            "breakdown": breakdown,
            "feedback": " ".join(feedback_parts),
        }

    # Decision correctness (0.15)
    if terminal_action["action_type"] == ground_truth["correct_decision"]:
        breakdown["decision_correctness"] = 0.15
        feedback_parts.append("Correct decision: denied.")
    else:
        feedback_parts.append(
            f"CRITICAL: Wrong decision: {terminal_action['action_type']}. Should have denied — patient has active contraindication."
        )
        breakdown["penalties"] -= 0.1
        feedback_parts.append("Major penalty: approving a patient with active surgical contraindication (-0.10).")

    # Contraindication found (0.25) — STRICT: must reference specific values
    rationale = (terminal_action.get("rationale") or "").lower()
    all_action_text = " ".join(
        (a.get("rationale") or "") + " " + str(a.get("payload", {}))
        for a in actions_taken
    ).lower()
    combined_text = rationale + " " + all_action_text

    has_hba1c_value = any(v in combined_text for v in ["8.4", "hba1c"])
    has_threshold = any(v in combined_text for v in ["8.0", "> 8", ">8", "threshold"])
    has_diabetes_concept = any(v in combined_text for v in ["diabetes", "uncontrolled", "glycemic"])
    has_contraindication_word = any(v in combined_text for v in ["contraindication", "contraindicated"])
    has_clearance = "surgical clearance" in combined_text or "not cleared" in combined_text

    contra_signals = sum([has_hba1c_value, has_threshold, has_diabetes_concept, has_contraindication_word, has_clearance])

    if has_hba1c_value and has_threshold and has_diabetes_concept:
        breakdown["contraindication_found"] = 0.25
        feedback_parts.append("Correctly identified contraindication: HbA1c 8.4% > 8.0% threshold (uncontrolled diabetes).")
    elif contra_signals >= 3:
        breakdown["contraindication_found"] = 0.15
        feedback_parts.append("Partially identified contraindication — missing specific HbA1c values.")
    elif contra_signals >= 2:
        breakdown["contraindication_found"] = 0.08
        feedback_parts.append("Vaguely referenced contraindication but lacked specifics.")
    else:
        feedback_parts.append("FAILED to identify the key contraindication (HbA1c 8.4% exceeds 8.0% surgical threshold).")

    # Guideline conflict resolution (0.15)
    correct_gl = ground_truth["applicable_guideline"].lower()
    conflicting_gl = ground_truth.get("conflicting_guideline", "").lower()

    mentions_correct = correct_gl in combined_text
    mentions_conflicting = conflicting_gl in combined_text

    if mentions_correct and not mentions_conflicting:
        breakdown["guideline_conflict_resolved"] = 0.15
        feedback_parts.append("Correctly identified GL-SPINE-003 as the applicable guideline.")
    elif mentions_correct and mentions_conflicting:
        if correct_gl in rationale:
            breakdown["guideline_conflict_resolved"] = 0.12
            feedback_parts.append("Identified both guidelines and correctly applied GL-SPINE-003.")
        else:
            breakdown["guideline_conflict_resolved"] = 0.05
            feedback_parts.append("Referenced both guidelines but unclear which was applied.")
    elif mentions_conflicting and not mentions_correct:
        breakdown["guideline_conflict_resolved"] = 0.0
        feedback_parts.append("Applied wrong guideline (GL-SPINE-004 instead of GL-SPINE-003).")
    else:
        breakdown["guideline_conflict_resolved"] = 0.0
        feedback_parts.append("Did not reference any specific guideline for the denial.")

    # Denial code quality (0.15)
    denial_payload = terminal_action.get("payload", {})
    agent_denial_code = (
        denial_payload.get("reason_code", "")
        or denial_payload.get("denial_code", "")
    ).upper()
    correct_code = ground_truth["correct_denial_code"]
    alt_codes = [c.upper() for c in ground_truth.get("alternative_denial_codes", [])]

    if agent_denial_code == correct_code:
        breakdown["denial_code_quality"] = 0.15
        feedback_parts.append(f"Correct denial reason code: {correct_code}.")
    elif agent_denial_code in alt_codes:
        breakdown["denial_code_quality"] = 0.07
        feedback_parts.append(f"Acceptable but suboptimal denial code: {agent_denial_code} (best: {correct_code}).")
    elif terminal_action["action_type"] == "deny" and agent_denial_code:
        breakdown["denial_code_quality"] = 0.03
        feedback_parts.append(f"Denial code '{agent_denial_code}' is not appropriate for this case.")
    elif terminal_action["action_type"] == "deny":
        breakdown["denial_code_quality"] = 0.0
        feedback_parts.append("Denied but provided no reason code.")
    else:
        feedback_parts.append("No denial code (decision was not deny).")

    # Rationale quality (0.15) — strict for hard task
    rationale_score = _check_rationale_references(
        terminal_action.get("rationale"),
        ground_truth["key_findings"],
        ground_truth["applicable_guideline"],
    )
    breakdown["rationale_quality"] = round(0.15 * rationale_score, 4)
    if rationale_score >= 0.6:
        feedback_parts.append("Strong rationale addressing guideline criteria and contraindication.")
    elif rationale_score >= 0.3:
        feedback_parts.append("Rationale partially addresses the case complexity.")
    else:
        feedback_parts.append("Rationale insufficient — must address guideline, contraindication, and met criteria.")

    # Process quality (0.15) — MUST investigate before deciding on hard case
    process_score = 0.0
    if guideline_looked_up:
        process_score += 0.06
    else:
        feedback_parts.append("Guideline not consulted on a complex case — major process gap.")

    if patient_history_checked:
        process_score += 0.06
    else:
        feedback_parts.append("Patient history not reviewed on a case with relevant surgical history.")

    investigation_steps = sum(
        1 for a in action_sequence
        if a in ("lookup_guideline", "get_patient_history", "check_formulary", "request_info")
    )
    if investigation_steps >= 2:
        process_score += 0.03
    breakdown["process_quality"] = round(min(0.15, process_score), 4)

    # Penalties
    if repeated_actions > 0:
        penalty = min(0.2, repeated_actions * 0.1)
        breakdown["penalties"] -= penalty
        feedback_parts.append(f"Penalty: {repeated_actions} repeated action(s) (-{penalty:.2f}).")

    total = sum(breakdown.values())
    total = _normalize(total)

    return {
        "score": round(total, 4),
        "breakdown": {k: round(v, 4) for k, v in breakdown.items()},
        "feedback": " ".join(feedback_parts),
    }


GRADERS = {
    "easy_knee_mri": grade_easy,
    "medium_humira_crohns": grade_medium,
    "hard_spinal_fusion": grade_hard,
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
