"""
Medical Prior Authorization - Inference Script
===================================
STDOUT FORMAT:
 [START] task=<task_name> env=med_pa model=<model_name>
 [STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
 [END] success=<true|false> steps=<n> rewards=<r1,r2,...,rn>
"""

import asyncio
import json
import os
import re
import textwrap
from typing import Any, Dict, List, Optional

from openai import OpenAI

from client import MedPAEnv
from models import PAAction

LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
HF_TOKEN = os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")
BENCHMARK = "med_pa"
MAX_STEPS = 8

TASKS = [
    "easy_knee_mri", "easy_chest_xray", "easy_pt_eval",
    "medium_humira", "medium_ozempic", "medium_sleep_study",
    "hard_spinal_fusion", "hard_cardiac_cath", "hard_gene_therapy",
]

SYSTEM_PROMPT = textwrap.dedent("""\
You are an insurance prior authorization reviewer AI. You review medical procedure
requests against clinical guidelines and make coverage decisions.

Available actions (respond with EXACTLY ONE JSON object per turn):
1. {"action_type": "lookup_guideline", "payload": {"procedure": "<CPT>", "diagnosis": "<ICD-10>"}, "rationale": null}
2. {"action_type": "get_patient_history", "payload": {}, "rationale": null}
3. {"action_type": "check_formulary", "payload": {"drug": "<drug_name>"}, "rationale": null}
4. {"action_type": "request_info", "payload": {"fields": ["field1", "field2"]}, "rationale": "reason for request"}
5. {"action_type": "approve", "payload": {}, "rationale": "detailed rationale citing guideline ID and criteria met"}
6. {"action_type": "deny", "payload": {"reason_code": "CODE"}, "rationale": "detailed rationale citing guideline ID and unmet criteria"}

Valid denial reason codes: CONTRAINDICATION_ACTIVE, CRITERIA_NOT_MET, MEDICAL_NECESSITY_NOT_ESTABLISHED, SAFETY_CONCERN, STEP_THERAPY_NOT_COMPLETED

Strategy:
1. First, lookup the applicable guideline for the procedure/diagnosis
2. For drug/biologic requests: ALSO run check_formulary after lookup_guideline
3. Check if required documentation is present
4. If docs are missing, request them with request_info
5. Review all evidence against guideline criteria — look for buried contraindications
6. Make your decision with a detailed rationale citing the guideline ID

IMPORTANT: Respond with ONLY a valid JSON object. No extra text, no markdown.
""")


def log_start(task: str) -> None:
    print(f"[START] task={task} env={BENCHMARK} model={MODEL_NAME}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error or 'null'}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)


def build_user_prompt(obs: Any, step: int, history: List[str]) -> str:
    """Structure observation data into a clear prompt for the LLM."""
    patient = obs.patient or {}
    parts = [
        f"=== PA Review Case: {obs.request_id} (Step {step}/{MAX_STEPS}) ===",
        f"Patient: {patient.get('age', '?')}yo {patient.get('sex', '?')}, Plan: {patient.get('insurance_plan', '?')}",
        f"Diagnosis (ICD-10): {', '.join(obs.diagnosis) if obs.diagnosis else 'N/A'}",
        f"Procedure (CPT): {obs.procedure}",
        f"\nClinical Notes:\n{obs.clinical_notes}",
        f"\nPrior Treatments: {'; '.join(obs.prior_treatments) if obs.prior_treatments else 'None'}",
        f"Attached Documents: {', '.join(obs.attachments) if obs.attachments else 'None'}",
    ]
    if obs.guideline_result:
        parts.append(f"\n--- Guideline Lookup Result ---\n{obs.guideline_result}")
    if obs.formulary_result:
        parts.append(f"\n--- Formulary Check Result ---\n{obs.formulary_result}")
    if obs.patient_history_result:
        parts.append(f"\n--- Patient History ---\n{obs.patient_history_result}")
    if obs.info_request_result:
        parts.append(f"\n--- Requested Information ---\n{obs.info_request_result}")
    if obs.message:
        parts.append(f"\nStatus: {obs.message}")
    if history:
        parts.append("\nPrevious actions:")
        for h in history[-5:]:
            parts.append(f"  {h}")
    if hasattr(obs, 'available_actions') and obs.available_actions:
        parts.append(f"\nAvailable actions: {', '.join(obs.available_actions)}")
    steps_remaining = MAX_STEPS - step
    if steps_remaining <= 1:
        parts.append("\n⚠️ WARNING: Only 1 step remaining. You MUST make a terminal decision (approve/deny/request_info) NOW.")
    parts.append("\nRespond with ONE JSON action object:")
    return "\n".join(parts)


def parse_action(text: str) -> Dict[str, Any]:
    """Extract JSON action from model response."""
    text = text.strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {"action_type": "lookup_guideline", "payload": {"procedure": "unknown"}, "rationale": "fallback"}


async def llm_call(client: OpenAI, messages: list) -> str:
    """Make an LLM call with a 30s timeout."""
    def _call():
        resp = client.chat.completions.create(
            model=MODEL_NAME, messages=messages,
            temperature=0.3, max_tokens=1024, stream=False,
        )
        return (resp.choices[0].message.content or "").strip()
    try:
        return await asyncio.wait_for(asyncio.to_thread(_call), timeout=30)
    except Exception as exc:
        print(f"[DEBUG] LLM call failed: {exc}", flush=True)
        return '{"action_type": "lookup_guideline", "payload": {"procedure": "unknown"}, "rationale": "fallback"}'


async def run_task(client: OpenAI, env: MedPAEnv, task_name: str) -> float:
    """Run a single task with 90s timeout. Returns final grader score (0.0-1.0)."""
    rewards: List[float] = []
    history: List[str] = []
    steps_taken = 0
    success = False

    log_start(task_name)
    try:
        result = await env.reset(task_id=task_name)
        obs = result.observation

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            prompt = build_user_prompt(obs, step, history)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            llm_text = await llm_call(client, messages)
            action_dict = parse_action(llm_text)
            action_type = action_dict.get("action_type", "unknown")

            action = PAAction(**action_dict)
            result = await env.step(action)
            obs = result.observation

            reward = result.reward or 0.0
            done = result.done
            error = obs.last_action_error

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action_type, reward=reward, done=done, error=error)
            history.append(f"Step {step}: {action_type} -> reward={reward:.2f}")

            if done:
                break

        # Score = best reward from grader (terminal action fires the grader)
        # Use strict open interval (0.01, 0.99) — validator rejects exactly 0.0 or 1.0
        score = max(0.01, min(0.99, max(rewards))) if rewards else 0.01
        success = score >= 0.3

    except Exception as e:
        print(f"[DEBUG] Task error: {e}", flush=True)
        score = 0.01
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


async def run_task_with_timeout(client: OpenAI, env: MedPAEnv, task_name: str) -> float:
    """Wrap run_task with a 90s timeout."""
    try:
        return await asyncio.wait_for(run_task(client, env, task_name), timeout=90)
    except asyncio.TimeoutError:
        print(f"[DEBUG] Task {task_name} timed out (90s)", flush=True)
        log_end(success=False, steps=0, score=0.01, rewards=[])
        return 0.01


async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    if LOCAL_IMAGE_NAME:
        env = await MedPAEnv.from_docker_image(LOCAL_IMAGE_NAME)
    else:
        env = MedPAEnv(base_url=ENV_BASE_URL)
        await env.connect()

    try:
        scores = []
        for task in TASKS:
            s = await run_task_with_timeout(client, env, task)
            scores.append(s)
        avg = sum(scores) / len(scores) if scores else 0.0
        print(f"\n[SUMMARY] avg_score={avg:.3f} scores={','.join(f'{s:.3f}' for s in scores)}", flush=True)
    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"[END] success=false steps=0 score=0.01 rewards=", flush=True)
        print(f"[DEBUG] Fatal: {exc}", flush=True)
