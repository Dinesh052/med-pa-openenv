---
title: Medical Prior Authorization Environment
emoji: 🏥
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
tags:
  - openenv
---

# Medical Prior Authorization Environment (med_pa)

Simulates insurance prior authorization review. An agent reviews PA requests against clinical guidelines and makes approve/deny/request_info decisions. Models a $50B+ US healthcare administrative burden.

## Environment Description

**Prior Authorization (PA)** is the process by which health insurers require pre-approval before covering a prescribed medication, procedure, or service. It exists to control costs and ensure medical necessity, but in practice it creates enormous administrative overhead — physicians spend an estimated 34 hours per week on PA-related paperwork, delaying patient care and contributing to over $50 billion in annual US healthcare administrative waste.

This environment presents the agent with a PA request containing patient demographics, diagnosis codes (ICD-10), procedure codes (CPT), clinical notes, and prior treatment history. The agent must gather relevant information (clinical guidelines, formulary status, patient history), reason about medical necessity, and render a decision.

**Episode flow:**

1. Agent receives an initial observation with the PA request details.
2. Agent may take information-gathering actions (`lookup_guideline`, `check_formulary`, `get_patient_history`).
3. Results of each action are returned in the next observation.
4. Agent renders a terminal decision (`approve`, `deny`, or `request_info`) with a rationale.
5. Episode ends on a terminal action or after **8 steps** (whichever comes first).

## Action Space

| Action | Description | Payload Format |
|---|---|---|
| `approve` | Approve the PA request | `{"rationale": "string"}` |
| `deny` | Deny the PA request | `{"rationale": "string", "denial_reason": "string"}` |
| `request_info` | Request additional information from the provider | `{"info_needed": ["string"], "rationale": "string"}` |
| `lookup_guideline` | Retrieve clinical guidelines for a diagnosis/procedure | `{"guideline_id": "string"}` or `{"procedure_code": "string", "diagnosis_code": "string"}` |
| `check_formulary` | Check drug formulary status and requirements | `{"drug_name": "string"}` |
| `get_patient_history` | Retrieve patient's prior authorization and treatment history | `{"patient_id": "string"}` |

Terminal actions: `approve`, `deny`, `request_info`. Information-gathering actions: `lookup_guideline`, `check_formulary`, `get_patient_history`.

## Observation Space

| Field | Type | Description |
|---|---|---|
| `request_id` | `string` | Unique PA request identifier |
| `patient` | `object` | Patient demographics (id, name, age, sex, insurance plan) |
| `diagnosis` | `object` | ICD-10 code and description |
| `procedure` | `object` | CPT code and description |
| `clinical_notes` | `string` | Physician's clinical notes supporting the request |
| `prior_treatments` | `list[object]` | Previous treatments, medications, and outcomes |
| `attachments` | `list[string]` | References to attached documents (imaging, lab results) |
| `guidelines_retrieved` | `list[object]` | Clinical guidelines returned by `lookup_guideline` (initially empty) |
| `formulary_result` | `object \| null` | Formulary lookup result from `check_formulary` |
| `patient_history` | `object \| null` | Patient history from `get_patient_history` |
| `last_action_result` | `object \| null` | Result/status of the most recent action |
| `available_actions` | `list[string]` | Actions the agent can take in the current step |

## Tasks

| Task | Difficulty | Scenario | Key Challenge |
|---|---|---|---|
| `easy_knee_mri` | Easy | Knee MRI for ACL injury — positive Lachman test, 6 weeks PT | Straightforward approval with clear criteria met |
| `easy_chest_xray` | Easy | Chest X-ray for persistent cough — 5 weeks, failed empiric treatment | Simple approval, all criteria documented |
| `easy_pt_eval` | Easy | PT evaluation for rotator cuff tear — MRI-confirmed, functional limitation | Clear approval with documented pathology |
| `medium_humira` | Medium | Humira for Crohn's disease — CDAI 285, vague biologic mention | Missing step-therapy documentation; must request info |
| `medium_ozempic` | Medium | Semaglutide for T2DM+obesity — metformin intolerance, incomplete records | Missing lifestyle modification records and intolerance documentation |
| `medium_sleep_study` | Medium | In-lab polysomnography — failed home test, complex comorbidities | Approve despite failed prior test; must recognize valid clinical justification |
| `hard_spinal_fusion` | Hard | Spinal fusion — BMI 38, buried MRSA infection, conflicting guidelines | Buried contraindication (active infection) + conflicting guidelines |
| `hard_cardiac_cath` | Hard | Cardiac catheterization — positive stress test but eGFR 22, recent GI bleed | Multiple buried contraindications (renal failure + active bleeding risk) |
| `hard_gene_therapy` | Hard | Zolgensma for SMA — age-eligible but elevated transaminases | Buried hepatic contraindication in a high-stakes $2.1M gene therapy |

## Reward Function

**Reward components (sum to 1.0 max):**

| Component | Weight | Description |
|---|---|---|
| Decision correctness | +0.5 | Correct terminal action matches ground truth |
| Rationale quality | +0.2 | Rationale references relevant clinical criteria and codes |
| Correct info requested | +0.2 | Appropriate information-gathering actions taken (or correct info fields requested) |
| Efficiency | +0.1 | Fewer steps to reach correct decision |

**Penalties:**

| Penalty | Value | Trigger |
|---|---|---|
| Hallucinated guideline | -0.3 | Rationale cites a guideline that doesn't exist |
| Repeated actions | -0.2 | Same action with same payload taken more than once |

## Setup & Usage

```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
python inference.py
```

## Docker

```bash
docker build -t med-pa-env .
docker run -p 8000:8000 med-pa-env
```

## Baseline Scores

| Task | Expected Score |
|---|---|
| `easy_knee_mri` | 0.85–1.0 |
| `easy_chest_xray` | 0.85–1.0 |
| `easy_pt_eval` | 0.85–1.0 |
| `medium_humira` | 0.60–0.80 |
| `medium_ozempic` | 0.55–0.75 |
| `medium_sleep_study` | 0.60–0.80 |
| `hard_spinal_fusion` | 0.30–0.60 |
| `hard_cardiac_cath` | 0.25–0.55 |
| `hard_gene_therapy` | 0.20–0.50 |
