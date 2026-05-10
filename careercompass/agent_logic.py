from __future__ import annotations

import json
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
from careercompass.llm_client import call_openai_json
from careercompass.prompts import build_specialist_prompt
from careercompass.schemas import (
    InterviewEvaluation,
    InterviewQuestion,
    MarketSkill,
    ResumeRecommendation,
    RoadmapPhase,
    SkillGap,
)
from careercompass.state import AgentName, AgentState


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


def run_market_demand_logic(state: AgentState, profile: dict[str, Any]) -> list[MarketSkill]:
    return _run_list_agent_or_fallback(
        "market_demand",
        state,
        profile,
        lambda: market_skill_fallback(profile),
    )


def run_gap_analysis_logic(state: AgentState, profile: dict[str, Any]) -> list[SkillGap]:
    return _run_list_agent_or_fallback(
        "gap_analysis",
        state,
        profile,
        lambda: gap_report_fallback(profile),
    )


def run_curriculum_logic(state: AgentState, profile: dict[str, Any]) -> list[RoadmapPhase]:
    return _run_list_agent_or_fallback(
        "curriculum",
        state,
        profile,
        lambda: roadmap_fallback(profile),
    )


def run_resume_optimization_logic(state: AgentState, profile: dict[str, Any]) -> list[ResumeRecommendation]:
    return _run_list_agent_or_fallback(
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
    return interview_question_fallback(target_role, company, scenario, profile)


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

    return value


def _run_list_agent_or_fallback(
    agent_name: AgentName,
    state: AgentState,
    profile: dict[str, Any],
    fallback_factory,
) -> list[dict[str, Any]]:
    prompt = _build_prompt_for_future_llm(agent_name, state, profile)

    try:
        raw_response = call_openai_json(prompt)
    except Exception:
        return fallback_factory()

    if not raw_response:
        return fallback_factory()

    try:
        payload = parse_json_object(raw_response)
        return validate_agent_output(agent_name, payload)
    except (json.JSONDecodeError, ValueError, TypeError):
        return fallback_factory()


def _build_prompt_for_future_llm(agent_name: AgentName, state: AgentState, profile: dict[str, Any]) -> str:
    """Central hook for replacing deterministic fallbacks with real model calls."""

    return build_specialist_prompt(agent_name, state, profile)
