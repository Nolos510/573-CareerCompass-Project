from __future__ import annotations

from typing import Literal, TypedDict


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

