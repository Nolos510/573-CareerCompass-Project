from __future__ import annotations

from typing import Any


def market_skill_fallback(profile: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"Skill": skill, "Demand Signal": demand, "Evidence": evidence}
        for skill, demand, evidence in profile["skills"]
    ]


def gap_report_fallback(profile: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "Skill": skill,
            "Current Evidence": evidence,
            "Severity": severity,
            "Recommendation": recommendation,
            "First Step": profile["gap_deep_dives"][skill]["first_steps"][0],
            "Resume Proof": profile["gap_deep_dives"][skill]["resume_proof"],
        }
        for skill, evidence, severity, recommendation in profile["gaps"]
    ]


def roadmap_fallback(profile: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "period": period,
            "goal": goal,
            "tasks": tasks,
            "resource_relevance": relevance,
        }
        for period, goal, tasks, relevance in profile["roadmap"]
    ]


def resume_recommendation_fallback(profile: dict[str, Any]) -> list[dict[str, Any]]:
    if "Project Manager" in profile["label"] and "Business Analyst" not in profile["label"]:
        return [
            {
                "before": "Led a team project documenting business requirements and presenting recommendations to stakeholders.",
                "after": (
                    "Coordinated a cross-functional class project by defining scope, tracking milestones, documenting risks, "
                    "and presenting stakeholder-ready recommendations."
                ),
                "keywords_added": ["scope", "milestones", "risks", "stakeholder-ready"],
            },
            {
                "before": "Worked on class analytics project using data tools to make charts and explain findings.",
                "after": (
                    "Managed a project workstream for an analytics deliverable, aligning team responsibilities, deadlines, "
                    "and final presentation outcomes."
                ),
                "keywords_added": ["managed", "workstream", "deadlines", "deliverable"],
            },
        ]

    return [
        {
            "before": "Built class analytics project using spreadsheet models and dashboard charts to explain sales performance trends.",
            "after": (
                "Built a business analytics dashboard to identify sales performance trends, translate KPIs into "
                "stakeholder recommendations, and support data-driven decision-making."
            ),
            "keywords_added": ["business analytics", "dashboard", "KPIs", "stakeholder recommendations"],
        },
        {
            "before": "Designed a database schema and wrote SQL queries for a course registration management case.",
            "after": (
                "Designed a relational database schema and wrote SQL queries to analyze course registration patterns, "
                "improving reporting clarity for academic planning decisions."
            ),
            "keywords_added": ["relational database", "SQL queries", "analyze", "reporting"],
        },
    ]


def interview_question_fallback(target_role: str, company: str, scenario: str, profile: dict[str, Any]) -> list[dict[str, Any]]:
    company = company.strip() or "the target company"
    scenario = scenario.strip() or profile["default_interview_scenario"]

    return [
        {
            "type": "Behavioral",
            "question": (
                f"At {company}, how would you describe a time you handled a similar situation: {scenario}"
            ),
            "rubric_focus": "STAR structure, stakeholder framing, measurable result",
        },
        {
            "type": "Technical",
            "question": profile["technical_question"],
            "rubric_focus": profile["technical_rubric"],
        },
        {
            "type": "Scenario",
            "question": (
                f"Imagine {company} gives you this case: {scenario} What steps would you take in your first week?"
            ),
            "rubric_focus": "clarifying questions, prioritization, evidence, risk management",
        },
    ]


def sample_interview_answer(question: str, rubric_focus: str) -> str:
    return (
        "In a class analytics project, my team had unclear stakeholder expectations for what the final dashboard should show. "
        "I clarified the business question, grouped requirements into must-have and nice-to-have metrics, and built a simple "
        "analysis plan before creating the final deliverable. I then presented the recommendation in terms of decision impact, "
        "not just charts. The result was a clearer final presentation and a dashboard that connected the data work to a specific "
        f"business decision. This answer works because it addresses {rubric_focus}."
    )


def interview_evaluation_fallback(question: str, answer: str, rubric_focus: str) -> dict[str, Any]:
    answer_lower = answer.lower()
    signals = {
        "situation": any(word in answer_lower for word in ["situation", "context", "problem", "challenge"]),
        "action": any(word in answer_lower for word in ["i did", "i built", "i led", "i analyzed", "action"]),
        "result": any(word in answer_lower for word in ["result", "impact", "improved", "reduced", "increased", "%"]),
        "stakeholder": any(word in answer_lower for word in ["stakeholder", "client", "manager", "team", "user"]),
        "specific": len(answer.split()) >= 70,
    }
    score = min(1 + sum(signals.values()), 5)

    missing = [name for name, present in signals.items() if not present]
    if not answer.strip():
        feedback = "No answer entered yet. Add a STAR-style response, then evaluate again."
        score = 0
    elif missing:
        feedback = (
            f"Good start. To improve, add more evidence for: {', '.join(missing)}. "
            f"Rubric focus: {rubric_focus}."
        )
    else:
        feedback = (
            "Strong answer. It includes context, action, result, stakeholder value, and enough detail to sound credible."
        )

    return {
        "score": score,
        "feedback": feedback,
        "sample_answer": sample_interview_answer(question, rubric_focus),
    }
