from __future__ import annotations

import json
import os
import re
from typing import Any

from careercompass.fallbacks import (
    gap_report_fallback,
    interview_evaluation_fallback,
    interview_question_fallback,
    market_skill_fallback,
    resume_recommendation_fallback,
    roadmap_fallback,
)
from careercompass.prompts import build_specialist_prompt
from careercompass.schemas import (
    InterviewEvaluation,
    InterviewQuestion,
    MarketSkill,
    ResumeRecommendation,
    RoadmapPhase,
    SkillGap,
    response_format_for_agent,
)
from careercompass.state import AgentName, AgentState


DEFAULT_OPENAI_MODEL = "gpt-5.4-mini"

AGENT_OUTPUT_KEYS: dict[AgentName, str] = {
    "supervisor": "route_plan",
    "market_demand": "market_skills",
    "gap_analysis": "gap_report",
    "curriculum": "learning_roadmap",
    "resume_optimization": "resume_recommendations",
    "interview_simulation": "interview_questions",
    "synthesis": "final_strategy_report",
}

REQUIRED_RECORD_KEYS: dict[AgentName, set[str]] = {
    "market_demand": {"Skill", "Demand Signal", "Evidence"},
    "gap_analysis": {"Skill", "Current Evidence", "Severity", "Recommendation", "First Step", "Resume Proof"},
    "curriculum": {"period", "goal", "tasks", "resource_relevance"},
    "resume_optimization": {"before", "after", "keywords_added"},
    "interview_simulation": {"type", "question", "rubric_focus"},
}

ALLOWED_VALUES: dict[str, set[str]] = {
    "Demand Signal": {"Very high", "High", "Medium", "Low"},
    "Severity": {"High", "Medium", "Low"},
    "type": {"Behavioral", "Technical", "Scenario"},
}


def run_market_demand_logic(state: AgentState, profile: dict[str, Any]) -> list[MarketSkill]:
    return _run_structured_agent(
        "market_demand",
        state,
        profile,
        lambda: market_skill_fallback(profile),
    )


def run_gap_analysis_logic(state: AgentState, profile: dict[str, Any]) -> list[SkillGap]:
    return _run_structured_agent(
        "gap_analysis",
        state,
        profile,
        lambda: gap_report_fallback(profile),
    )


def run_curriculum_logic(state: AgentState, profile: dict[str, Any]) -> list[RoadmapPhase]:
    return _run_structured_agent(
        "curriculum",
        state,
        profile,
        lambda: roadmap_fallback(profile),
    )


def run_resume_optimization_logic(state: AgentState, profile: dict[str, Any]) -> list[ResumeRecommendation]:
    return _run_structured_agent(
        "resume_optimization",
        state,
        profile,
        lambda: resume_recommendation_fallback(profile),
    )


def run_interview_question_logic(
    target_role: str,
    company: str,
    scenario: str,
    profile: dict[str, Any],
) -> list[InterviewQuestion]:
    state = _interview_state(target_role, company, scenario)
    return _run_structured_agent(
        "interview_simulation",
        state,
        profile,
        lambda: interview_question_fallback(target_role, company, scenario, profile),
    )


def run_interview_evaluation_logic(question: str, answer: str, rubric_focus: str) -> InterviewEvaluation:
    return interview_evaluation_fallback(question, answer, rubric_focus)


def parse_json_object(raw_text: str) -> dict[str, Any]:
    """Parse a JSON object, accepting common fenced-code responses from LLMs."""

    cleaned = raw_text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()

    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("Agent output must be a JSON object.")
    return payload


def validate_agent_output(agent_name: AgentName, payload: dict[str, Any]) -> Any:
    """Validate a parsed model payload before it enters AgentState."""

    output_key = AGENT_OUTPUT_KEYS[agent_name]
    if output_key not in payload:
        raise ValueError(f"Missing required output key: {output_key}")

    value = payload[output_key]
    if agent_name == "synthesis":
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Synthesis output must be a non-empty string.")
        return value

    if agent_name == "supervisor":
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError("Supervisor route_plan must be a list of agent names.")
        return value

    required_keys = REQUIRED_RECORD_KEYS[agent_name]
    if not isinstance(value, list) or not value:
        raise ValueError(f"{output_key} must be a non-empty list.")

    for index, record in enumerate(value, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"{output_key}[{index}] must be an object.")
        missing = required_keys.difference(record)
        if missing:
            missing_keys = ", ".join(sorted(missing))
            raise ValueError(f"{output_key}[{index}] missing required keys: {missing_keys}")
        _validate_record_values(output_key, index, record)

    return value


def _run_structured_agent(
    agent_name: AgentName,
    state: AgentState,
    profile: dict[str, Any],
    fallback: Any,
) -> Any:
    """Run an OpenAI-backed agent when configured, otherwise use fallback data."""

    if not _llm_enabled() or not os.getenv("OPENAI_API_KEY"):
        return fallback()

    try:
        payload = _call_openai_structured_agent(agent_name, state, profile)
        return validate_agent_output(agent_name, payload)
    except Exception as exc:  # noqa: BLE001 - every model-path failure must fall back.
        _record_model_error(state, agent_name, exc)
        return fallback()


def _call_openai_structured_agent(
    agent_name: AgentName,
    state: AgentState,
    profile: dict[str, Any],
) -> dict[str, Any]:
    prompt = _build_prompt_for_llm(agent_name, state, profile)
    client = _create_openai_client()
    response = client.responses.create(
        model=_openai_model(),
        input=[
            {
                "role": "system",
                "content": (
                    "You produce privacy-conscious CareerCompass agent outputs. "
                    "Return only JSON that matches the provided schema."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        text={"format": response_format_for_agent(agent_name)},
    )
    output_text = _extract_response_text(response)
    if not output_text:
        raise ValueError("OpenAI response did not include output text.")
    return parse_json_object(output_text)


def _create_openai_client() -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI SDK is not installed.") from exc

    return OpenAI()


def _extract_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    for item in getattr(response, "output", []) or []:
        for part in _get_value(item, "content") or []:
            refusal = _get_value(part, "refusal")
            if refusal:
                raise ValueError("OpenAI response included a refusal.")
            text = _get_value(part, "text")
            if isinstance(text, str) and text.strip():
                return text

    return ""


def _get_value(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def _llm_enabled() -> bool:
    setting = os.getenv("CAREERCOMPASS_LLM_ENABLED", "true").strip().lower()
    return setting not in {"0", "false", "no", "off"}


def _openai_model() -> str:
    return os.getenv("CAREERCOMPASS_OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL


def _record_model_error(state: AgentState, agent_name: AgentName, exc: Exception) -> None:
    errors = state.setdefault("errors", [])
    message = _sanitize_error(str(exc) or exc.__class__.__name__)
    errors.append(f"{agent_name}: OpenAI structured output failed; used fallback. {message}")


def _sanitize_error(message: str) -> str:
    sanitized = re.sub(r"sk-[A-Za-z0-9_-]+", "sk-...", message)
    sanitized = re.sub(r"api[_ -]?key[=:]\s*['\"]?[^'\"\s]+", "api_key=...", sanitized, flags=re.IGNORECASE)
    return sanitized[:240]


def _validate_record_values(output_key: str, index: int, record: dict[str, Any]) -> None:
    for key, value in record.items():
        label = f"{output_key}[{index}].{key}"
        if key in {"tasks", "keywords_added"}:
            _require_string_list(value, label)
        else:
            _require_non_empty_string(value, label)

        allowed = ALLOWED_VALUES.get(key)
        if allowed and value not in allowed:
            allowed_values = ", ".join(sorted(allowed))
            raise ValueError(f"{label} must be one of: {allowed_values}")


def _require_non_empty_string(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string.")


def _require_string_list(value: Any, label: str) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list.")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{label} must contain only non-empty strings.")


def _interview_state(target_role: str, company: str, scenario: str) -> AgentState:
    return {
        "user_profile": {},
        "target_role": target_role,
        "target_location": "Not supplied",
        "timeline_days": 90,
        "resume_text": "",
        "coursework": [],
        "retrieved_job_postings": [],
        "market_skills": [],
        "gap_report": [],
        "learning_roadmap": [],
        "resume_recommendations": [],
        "interview_questions": [],
        "interview_feedback": [],
        "confidence_scores": {},
        "final_strategy_report": "",
        "workflow_intent": "interview_only",
        "route_plan": ["interview_simulation"],
        "completed_agents": [],
        "handoffs": [],
        "errors": [],
        "interview_company": company,
        "interview_scenario": scenario,
    }


def _build_prompt_for_llm(agent_name: AgentName, state: AgentState, profile: dict[str, Any]) -> str:
    """Central hook for OpenAI prompt construction."""

    return build_specialist_prompt(agent_name, state, profile)
