"""
Medical Prior Authorization - Inference Script
===================================
STDOUT FORMAT:
 [START] task=<task_name> env=med_pa model=<model_name>
 [STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
 [END] success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import asyncio
import json
import os
import re
import textwrap
from typing import List, Optional

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
TASKS = ["easy_knee_mri", "medium_humira", "hard_spinal_fusion"]

SYSTEM_PROMPT = textwrap.dedent("""
You are a medical prior authorization (PA) reviewer. Evaluate PA requests by gathering clinical guidelines, reviewing patient data, and making approve/deny/request_info decisions.

Available actions (respond with ONLY valid JSON, no other text):

1. lookup_guideline - Look up clinical guidelines by procedure or diagnosis code.
   {"action_type": "lookup_guideline", "payload": {"procedure": "<CPT code>"}, "rationale": "Looking up guidelines."}

2. check_formulary - Check drug formulary status.
   {"action_type": "check_formulary", "payload": {"drug": "<drug_name>"}, "rationale": "Checking formulary."}

3. get_patient_history - Retrieve patient history.
   {"action_type": "get_patient_history", "payload": {}, "rationale": "Retrieving history."}

4. approve - Approve the PA request (terminal).
   {"action_type": "approve", "payload": {}, "rationale": "Per GL-XXX: <rationale citing guideline IDs>"}

5. deny - Deny the PA request (terminal).
   {"action_type": "deny", "payload": {"reason_code": "<CODE>"}, "rationale": "Per GL-XXX: <rationale>"}

6. request_info - Request missing documentation (terminal).
   {"action_type": "request_info", "payload": {"fields": ["field1", "field2"]}, "rationale": "Per GL-XXX: <rationale>"}

Strategy:
1. FIRST lookup_guideline with the procedure code.
2. Analyze patient data and clinical notes against guideline criteria.
3. Look for contraindications, missing docs, or unmet criteria.
4. If docs missing, request_info. If contraindication, deny with reason_code. If criteria met, approve.
5. ALWAYS cite guideline IDs (GL-KNEE-MRI-001, GL-BIOLOGIC-001, etc.) in rationale.

Respond with ONLY a single JSON object.
""").strip()


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


def parse_action(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {"action_type": "lookup_guideline", "payload": {"procedure": "unknown"}, "rationale": "fallback"}


def get_llm_action(client: OpenAI, messages: list) -> str:
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME, messages=messages,
            temperature=0.2, max_tokens=512, stream=False,
        )
        return (completion.choices[0].message.content or "").strip()
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return '{"action_type": "lookup_guideline", "payload": {"procedure": "unknown"}, "rationale": "fallback"}'


async def run_task(llm: OpenAI, env: MedPAEnv, task_name: str) -> float:
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset(task_id=task_name)
        obs = result.observation

        obs_summary = json.dumps({
            "request_id": obs.request_id, "patient": obs.patient,
            "diagnosis": obs.diagnosis, "procedure": obs.procedure,
            "clinical_notes": obs.clinical_notes,
            "prior_treatments": obs.prior_treatments,
            "attachments": obs.attachments,
        }, indent=2)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Review this PA request:\n{obs_summary}\n\nStart by looking up the relevant clinical guideline using the procedure code."},
        ]

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            llm_text = get_llm_action(llm, messages)
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

            messages.append({"role": "assistant", "content": llm_text})

            if done:
                break

            # Build next prompt
            next_msg = f"Result: {obs.last_action_result}"
            if obs.guidelines_retrieved:
                next_msg += f"\nGuidelines: {json.dumps(obs.guidelines_retrieved)}"
            if obs.formulary_result:
                next_msg += f"\nFormulary: {json.dumps(obs.formulary_result)}"
            if obs.patient_history:
                next_msg += f"\nPatient history: {json.dumps(obs.patient_history)}"
            next_msg += "\n\nContinue your review. Respond with JSON only."
            messages.append({"role": "user", "content": next_msg})

        score = max(0.0, min(1.0, rewards[-1] if rewards else 0.0))
        success = score > 0 and result.done

    except Exception as e:
        print(f"[DEBUG] Task error: {e}", flush=True)
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


async def main() -> None:
    llm = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    if LOCAL_IMAGE_NAME:
        env = await MedPAEnv.from_docker_image(LOCAL_IMAGE_NAME)
    else:
        env = MedPAEnv(base_url=ENV_BASE_URL)
        await env.connect()

    try:
        scores = []
        for task in TASKS:
            s = await run_task(llm, env, task)
            scores.append(s)
        avg = sum(scores) / len(scores) if scores else 0.0
        print(f"\n[SUMMARY] avg_score={avg:.3f} scores={','.join(f'{s:.3f}' for s in scores)}", flush=True)
    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
