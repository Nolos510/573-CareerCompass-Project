# Agent Logic Handoff

This document covers the TM3 agent-logic lane: prompts, structured JSON outputs,
OpenAI model calls, and deterministic fallback behavior.

## Runtime Configuration

- `OPENAI_API_KEY`: enables live OpenAI calls when present.
- `CAREERCOMPASS_OPENAI_MODEL`: optional model override. Defaults to `gpt-5.4-mini`.
- `CAREERCOMPASS_LLM_ENABLED`: set to `false`, `0`, `no`, or `off` to force deterministic fallbacks.
- `CAREERCOMPASS_USE_LLM` and `CAREERCOMPASS_LLM_MODEL`: legacy toggles still work for branch compatibility.

Do not hardcode API keys in source, tests, docs, or PR comments. If a key is
shared outside a secret manager, rotate it before using the project again.

## Structured Outputs

Agent JSON contracts live in `careercompass/schemas.py` and are passed to the
OpenAI Responses API as strict JSON Schema formats. Runtime validation also
runs in `careercompass/agent_logic.py` before model output enters workflow
state.

Covered agent outputs:

- `market_skills`
- `gap_report`
- `learning_roadmap`
- `resume_recommendations`
- `interview_questions`
- `final_strategy_report`
- `route_plan`

## Fallback Behavior

The app remains demo-safe without a live model. Agent logic uses deterministic
fallbacks when:

- `OPENAI_API_KEY` is missing.
- `CAREERCOMPASS_LLM_ENABLED` disables model calls.
- The OpenAI SDK is not installed.
- The API call fails.
- The model returns empty text, invalid JSON, a refusal, or a schema-invalid payload.

When a live model path fails, the error is sanitized and appended to
`state["errors"]`; secrets are redacted before storage. Missing API keys and
explicitly disabled LLM calls do not add errors because those are expected demo
modes.

## Handoff Notes

Done:

- Centralized prompt templates include evidence boundaries and JSON-only rules.
- Strict JSON Schemas are available for each agent output.
- OpenAI calls use the Responses API through `careercompass/llm_client.py`.
- Deterministic and RAG-derived fallbacks still power local demos.
- Unit tests mock the OpenAI client and avoid network calls.

Still needed:

- Request CodeRabbit review on the PR.
- Run a quick secret/sensitive-data review before merge.

Questions:

- Should synthesis eventually move to live structured model output, or remain
  deterministic for demo stability?
