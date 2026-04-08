# Contributing

## Setup
```bash
pip install -e ".[dev]"
```

## Run the environment server
```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

## Run the agent
```bash
export HF_TOKEN=your_token_here
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
python inference.py
```

## Run all tests
```bash
pytest tests/ -v
```

## Docker
```bash
docker build -t med-pa-env .
docker run -p 8000:8000 med-pa-env
```

## Reward breakdown

The grader is in `grader.py`. To inspect a reward manually:

```python
from grader import grade_task

actions = [
    {"action_type": "lookup_guideline", "payload": {"procedure": "73721"}, "rationale": None},
    {"action_type": "approve", "payload": {}, "rationale": "Per GL-KNEE-MRI-001: positive Lachman test, 6 weeks PT completed"},
]
ground_truth = {
    "decision": "approve",
    "required_criteria": ["GL-KNEE-MRI-001"],
    "required_missing_fields": [],
    "denial_reason_code": None,
    "key_findings": ["positive Lachman test", "ACL disruption", "completed 6 weeks PT"],
}
result = grade_task("easy_knee_mri", actions, ground_truth)
print(result["score"], result["feedback"])
```
