from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict


AgentName = Literal[
    "supervisor",
    "market_demand",
    "gap_analysis",
    "curriculum",
    "resume_optimization",
    "interview_simulation",
    "synthesis",
]

WorkflowIntent = Literal["full_strategy", "resume_only", "interview_only"]


class AgentHandoff(TypedDict):
    """Structured handoff contract written between workflow nodes."""

    from_agent: AgentName
    to_agent: AgentName
    reason: str
    required_inputs: list[str]
    expected_outputs: list[str]
    status: Literal["queued", "completed", "skipped"]


class AgentState(TypedDict):
    """Shared state passed through the CareerCompass supervisor workflow."""

    user_profile: dict[str, Any]
    target_role: str
    target_location: str
    timeline_days: int
    resume_text: str
    coursework: list[str]
    retrieved_job_postings: list[dict[str, Any]]
    market_skills: list[dict[str, Any]]
    gap_report: list[dict[str, Any]]
    learning_roadmap: list[dict[str, Any]]
    resume_recommendations: list[dict[str, Any]]
    interview_questions: list[dict[str, Any]]
    interview_feedback: list[dict[str, Any]]
    confidence_scores: dict[str, float]
    final_strategy_report: str
    profile: NotRequired[dict[str, Any]]
    workflow_intent: NotRequired[WorkflowIntent]
    route_plan: NotRequired[list[AgentName]]
    completed_agents: NotRequired[list[AgentName]]
    handoffs: NotRequired[list[AgentHandoff]]
    errors: NotRequired[list[str]]
    final_output: NotRequired[dict[str, Any]]
