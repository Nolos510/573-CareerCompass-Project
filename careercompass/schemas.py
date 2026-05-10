from __future__ import annotations

from typing import Literal, TypedDict

from careercompass.state import AgentName


MarketSkill = TypedDict(
    "MarketSkill",
    {
        "Skill": str,
        "Demand Signal": str,
        "Evidence": str,
    },
)

SkillGap = TypedDict(
    "SkillGap",
    {
        "Skill": str,
        "Current Evidence": str,
        "Severity": Literal["High", "Medium", "Low"],
        "Recommendation": str,
        "First Step": str,
        "Resume Proof": str,
    },
)


class RoadmapPhase(TypedDict):
    period: str
    goal: str
    tasks: list[str]
    resource_relevance: str


class ResumeRecommendation(TypedDict):
    before: str
    after: str
    keywords_added: list[str]


class InterviewQuestion(TypedDict):
    type: Literal["Behavioral", "Technical", "Scenario"]
    question: str
    rubric_focus: str


class InterviewEvaluation(TypedDict):
    score: int
    feedback: str
    sample_answer: str


STRING_SCHEMA = {"type": "string", "minLength": 1}
STRING_ARRAY_SCHEMA = {
    "type": "array",
    "items": STRING_SCHEMA,
    "minItems": 1,
}


def _object_schema(properties: dict, required: list[str]) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _list_output_schema(output_key: str, item_properties: dict, required: list[str]) -> dict:
    return _object_schema(
        {
            output_key: {
                "type": "array",
                "items": _object_schema(item_properties, required),
                "minItems": 1,
            }
        },
        [output_key],
    )


AGENT_JSON_SCHEMAS: dict[AgentName, dict] = {
    "market_demand": _list_output_schema(
        "market_skills",
        {
            "Skill": STRING_SCHEMA,
            "Demand Signal": {"type": "string", "enum": ["Very high", "High", "Medium", "Low"]},
            "Evidence": STRING_SCHEMA,
        },
        ["Skill", "Demand Signal", "Evidence"],
    ),
    "gap_analysis": _list_output_schema(
        "gap_report",
        {
            "Skill": STRING_SCHEMA,
            "Current Evidence": STRING_SCHEMA,
            "Severity": {"type": "string", "enum": ["High", "Medium", "Low"]},
            "Recommendation": STRING_SCHEMA,
            "First Step": STRING_SCHEMA,
            "Resume Proof": STRING_SCHEMA,
        },
        ["Skill", "Current Evidence", "Severity", "Recommendation", "First Step", "Resume Proof"],
    ),
    "curriculum": _list_output_schema(
        "learning_roadmap",
        {
            "period": STRING_SCHEMA,
            "goal": STRING_SCHEMA,
            "tasks": STRING_ARRAY_SCHEMA,
            "resource_relevance": STRING_SCHEMA,
        },
        ["period", "goal", "tasks", "resource_relevance"],
    ),
    "resume_optimization": _list_output_schema(
        "resume_recommendations",
        {
            "before": STRING_SCHEMA,
            "after": STRING_SCHEMA,
            "keywords_added": STRING_ARRAY_SCHEMA,
        },
        ["before", "after", "keywords_added"],
    ),
    "interview_simulation": _list_output_schema(
        "interview_questions",
        {
            "type": {"type": "string", "enum": ["Behavioral", "Technical", "Scenario"]},
            "question": STRING_SCHEMA,
            "rubric_focus": STRING_SCHEMA,
        },
        ["type", "question", "rubric_focus"],
    ),
    "synthesis": _object_schema({"final_strategy_report": STRING_SCHEMA}, ["final_strategy_report"]),
    "supervisor": _object_schema(
        {
            "route_plan": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "market_demand",
                        "gap_analysis",
                        "curriculum",
                        "resume_optimization",
                        "interview_simulation",
                        "synthesis",
                    ],
                },
                "minItems": 1,
            }
        },
        ["route_plan"],
    ),
}


def response_format_for_agent(agent_name: AgentName) -> dict:
    """Return the OpenAI structured-output format for one agent."""

    return {
        "type": "json_schema",
        "name": f"careercompass_{agent_name}_output",
        "strict": True,
        "schema": AGENT_JSON_SCHEMAS[agent_name],
    }
