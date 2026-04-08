---
title: Operational Risk Incident Triage
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: OpenEnv operational incident triage environment
tags:
  - openenv
  - operations
  - logistics
  - risk
  - real-world
---

# Operational Risk Incident Triage

`Operational Risk Incident Triage` is a real-world OpenEnv environment where an agent behaves like an operations analyst reviewing synthetic incident bundles. The agent must separate already-documented failure patterns from plausible emerging issues, identify the most likely root-cause asset or interaction, and choose the right follow-up path.

The data is synthetic and intentionally deterministic so local testing, baseline runs, and judge-side evaluation are reproducible.

## Why This Scenario Works

Operational review teams spend a lot of time triaging noisy incident queues. Some events are known platform behaviors, some are real regressions, and some are confounded by multiple systems interacting in a way that the first reporter misattributes. That makes the environment useful for evaluating prioritization, causal judgment, and escalation quality in a realistic workflow.

## Environment Summary

| Item | Value |
|---|---|
| Environment name | `ops-risk` |
| Domain | Operations / logistics incident triage |
| Episode length | 1 step per task |
| Task count | 3 |
| Difficulties | Easy, Medium, Hard |
| Reward range | `0.0` to `1.0` |
| API | `reset()`, `step()`, `state()` |
| Server | FastAPI |

## Compatibility Note

The OpenEnv wire contract is intentionally stable. Some field names such as `suspect_drug` and `drug_interaction_db` are retained for compatibility with the starter contract and validator path, but they now carry operational meanings:

- `suspect_drug`: suspected root-cause asset or interaction
- `drug_interaction_db`: hardcoded operational reference context
- `reports`: synthetic incident records

## Action Space

| Field | Type | Allowed values | Meaning |
|---|---|---|---|
| `classification` | `str` | `new_signal`, `known_side_effect`, `noise`, `duplicate` | Overall incident judgment |
| `suspect_drug` | `str` | Free text | Suspected root-cause module or cross-system interaction |
| `severity_assessment` | `str` | `mild`, `moderate`, `severe`, `critical` | Operational severity |
| `recommended_action` | `str` | `escalate`, `log_and_monitor`, `dismiss`, `request_more_info` | Next operational move |
| `reasoning` | `str` | Free text | Explanation used for partial credit on the hard task |

## Observation Space

| Field | Type | Description |
|---|---|---|
| `task_id` | `str` | Current task identifier |
| `reports` | `List[IncidentRecord]` | Synthetic incident records for the scenario |
| `drug_interaction_db` | `dict` | Hardcoded operational reference material |
| `step_number` | `int` | Current step index |
| `max_steps` | `int` | Maximum number of steps in the episode |
| `feedback` | `Optional[str]` | Feedback after the previous action |

## Tasks

| Task | Difficulty | Scenario | Ground-truth goal |
|---|---|---|---|
| `known_signal_easy` | Easy | Transit guidance tunnel drift already documented across many recent incidents | Recognize a known issue and `log_and_monitor` |
| `cluster_signal_medium` | Medium | New warehouse navigation rollout shows a small coherent freeze cluster | Recognize a plausible emerging signal and `escalate` |
| `confounded_hard` | Hard | Sort-line overload is blamed on OCR, but the deeper issue is a `FlowManager` and `VisionPatch` interaction | Detect the interaction, classify as `new_signal`, and `escalate` |

## Reward Function

| Reward component | Value |
|---|---|
| Correct `classification` | `+0.25` |
| Correct `suspect_drug` | `+0.25` |
| Correct `severity_assessment` | `+0.25` |
| Correct `recommended_action` | `+0.25` |
| False alarm penalty | `-0.10` |
| Missed signal penalty | `-0.20` |
| Hard-task reasoning bonus | `+0.15` |

The final reward is clamped to `[0.0, 1.0]`.

## Project Layout

| Path | Purpose |
|---|---|
| `ops_sim/contracts.py` | Core typed compatibility models |
| `ops_sim/scenario_bank.py` | Synthetic scenario data |
| `ops_sim/scoring.py` | Task definitions and reward logic |
| `ops_sim/runtime.py` | Main environment runtime |
| `server/app.py` | OpenEnv-compatible app entrypoint |
| `inference.py` | Required baseline inference runner |
| `openenv.yaml` | OpenEnv metadata |
| `Dockerfile` | Container build |
| `tests/test_env.py` | Local checks |

Legacy root modules such as `env.py`, `tasks.py`, and `data.py` remain as thin compatibility shims.

## Running Locally

```bash
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 7860
```

Or with Docker:

```bash
docker build -t ops-risk-env .
docker run -p 7860:7860 ops-risk-env
```

Health check:

```text
http://localhost:7860/health
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/reset` | Starts a task and returns the initial observation |
| `POST` | `/step` | Submits the final agent action and returns observation, reward, done, info |
| `GET` | `/state` | Returns internal environment state summary |
| `GET` | `/tasks` | Lists available task ids |
| `GET` | `/health` | Health check endpoint |

## Baseline Inference Script

The submission runner is `inference.py`.

It:
- reads `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`, and optional `ENV_URL`
- uses the OpenAI client for all model calls
- runs all three tasks sequentially
- emits the required `[START]`, `[STEP]`, and `[END]` lines only

Required environment variables:

```bash
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export HF_TOKEN=hf_your_token_here
export ENV_URL=http://localhost:7860
```

Run:

```bash
python inference.py
```

## Validation

```bash
pytest tests/test_env.py -q
openenv validate
./validate-submission.sh https://your-space.hf.space
```
