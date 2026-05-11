from __future__ import annotations

import re
from typing import Any


SKILL_ALIASES = {
    "Agile": ["agile", "scrum", "sprint"],
    "Excel": ["excel", "spreadsheet", "spreadsheets"],
    "Jira": ["jira", "atlassian"],
    "KPIs": ["kpi", "kpis", "metric", "metrics"],
    "Power BI": ["power bi", "powerbi"],
    "Python": ["python"],
    "SQL": ["sql", "database", "queries", "query"],
    "Tableau": ["tableau"],
    "stakeholder communication": ["stakeholder", "stakeholders", "presentation", "communication"],
    "requirements gathering": ["requirements", "business requirements", "user stories"],
    "risk management": ["risk", "risks", "mitigation"],
    "project coordination": ["project coordination", "coordinated", "led a team", "team project"],
    "milestones": ["milestone", "milestones", "timeline", "schedule"],
    "documentation": ["documentation", "documenting", "documented"],
    "data analysis": ["data analysis", "analytics", "analysis"],
    "data storytelling": ["storytelling", "presenting findings", "recommendations"],
    "process improvement": ["process improvement", "improvement"],
    "process mapping": ["process mapping", "process map"],
    "user acceptance testing": ["uat", "user acceptance", "testing"],
    "business process": ["business process", "process"],
    "experimentation": ["experimentation", "experiment", "a/b"],
    "scope": ["scope", "scoping"],
    "Scrum": ["scrum", "sprint"],
    "timeline management": ["timeline", "schedule"],
    "presentation": ["presentation", "presented", "presenting"],
}


def market_skill_fallback(profile: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"Skill": skill, "Demand Signal": demand, "Evidence": evidence}
        for skill, demand, evidence in profile["skills"]
    ]


def gap_report_fallback(
    profile: dict[str, Any],
    state: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if state and state.get("market_skills"):
        dynamic_report = _dynamic_gap_report(profile, state)
        if dynamic_report:
            return dynamic_report

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


def _dynamic_gap_report(profile: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    evidence_text = _student_evidence_text(state)
    missing_rows = []
    covered_rows = []

    for market_skill in state.get("market_skills", [])[:8]:
        skill = market_skill["Skill"]
        evidenced = _skill_is_evidenced(skill, evidence_text)
        demand = market_skill.get("Demand Signal", "Medium")

        if evidenced:
            row = {
                "Skill": skill,
                "Current Evidence": f"Found evidence of {skill} in the resume or coursework.",
                "Severity": "Low",
                "Recommendation": f"Keep {skill} visible and add a measurable result or project outcome.",
                "First Step": f"Add one bullet that shows how {skill} supported a business or project decision.",
                "Resume Proof": f"Name {skill}, the project context, and the outcome it supported.",
            }
            covered_rows.append(row)
            continue

        severity = "High" if demand in {"Very high", "High"} else "Medium"
        row = {
            "Skill": skill,
            "Current Evidence": f"No clear {skill} evidence found in the supplied resume or coursework.",
            "Severity": severity,
            "Recommendation": f"Create or document a small project that proves {skill} for {state['target_role']} roles.",
            "First Step": f"Complete a short {skill} exercise and connect it to one target-role business case.",
            "Resume Proof": f"Add a resume bullet naming {skill}, the deliverable, and the recommendation or result.",
        }
        missing_rows.append(row)

    rows = missing_rows + covered_rows
    if rows:
        return rows

    return []


def skill_is_evidenced(skill: str, resume_text: str, coursework: list[str]) -> bool:
    return _skill_is_evidenced(skill, _normalize_text(f"{resume_text} {' '.join(coursework)}"))


def _student_evidence_text(state: dict[str, Any]) -> str:
    return _normalize_text(
        " ".join(
            [
                state.get("resume_text", ""),
                " ".join(state.get("coursework", [])),
            ]
        )
    )


def _skill_is_evidenced(skill: str, evidence_text: str) -> bool:
    for term in _skill_terms(skill):
        if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", evidence_text):
            return True
    return False


def _skill_terms(skill: str) -> list[str]:
    terms = [skill.lower()]
    terms.extend(SKILL_ALIASES.get(skill, []))
    if "/" in skill or " or " in skill.lower():
        terms.extend(re.split(r"\s*/\s*|\s+or\s+", skill.lower()))
    return [_normalize_text(term) for term in terms if term.strip()]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def roadmap_fallback(profile: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "period": period,
            "goal": goal,
            "tasks": tasks,
            "resource_relevance": str(relevance),
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
    company = _clean_company(company)
    scenario = scenario.strip() or profile["default_interview_scenario"]
    role_family = _interview_role_family(target_role, scenario)
    scenario_focus = _scenario_focus(scenario)
    summary = _scenario_summary(scenario, scenario_focus)
    company_context = _company_context(company)

    return _dedupe_questions(
        _question_bank(role_family, target_role, company, company_context, scenario_focus, summary, profile)
    )


def _clean_company(company: str) -> str:
    return company.strip() or "the target company"


def _clean_scenario_text(scenario: str) -> str:
    cleaned = re.sub(r"\s+", " ", scenario).strip()
    cleaned = re.sub(r"\b(Role|Interview Context|Scenario Details)\b\s*:?", "", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip(" -")


def _scenario_summary(scenario: str, focus: str) -> str:
    cleaned = _clean_scenario_text(scenario)
    if not cleaned:
        return focus

    sentences = [part.strip(" .") for part in re.split(r"(?<=[.!?])\s+|\n+", cleaned) if part.strip()]
    useful_terms = [
        "launch",
        "conversion",
        "dashboard",
        "metrics",
        "stakeholder",
        "requirements",
        "quality",
        "timeline",
        "risk",
        "customer",
        "onboarding",
        "campaign",
        "workflow",
    ]
    chosen: list[str] = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(term in sentence_lower for term in useful_terms):
            chosen.append(sentence)
        if len(" ".join(chosen)) >= 120:
            break
    if not chosen:
        chosen = sentences[:1]

    summary = ". ".join(chosen).strip()
    if not summary:
        return focus
    if len(summary) > 150:
        summary = summary[:147].rsplit(" ", 1)[0].rstrip(",.;:") + "..."
    return summary


def _scenario_focus(scenario: str) -> str:
    text = scenario.lower()
    if any(term in text for term in ["launch", "campaign", "conversion", "onboarding", "free trial"]):
        return "launch planning, customer insight, and conversion metrics"
    if any(term in text for term in ["data quality", "different numbers", "inconsistent", "duplicate"]):
        return "data quality, metric trust, and stakeholder alignment"
    if any(term in text for term in ["dashboard", "revenue", "acquisition", "kpi", "weekly user activity"]):
        return "dashboard performance and KPI tradeoffs"
    if any(term in text for term in ["requirements", "success metrics", "acceptance criteria"]):
        return "ambiguous requirements and measurable success criteria"
    if any(term in text for term in ["scope", "deadline", "timeline", "behind schedule", "dependency"]):
        return "delivery tradeoffs, scope control, and risk mitigation"
    if any(term in text for term in ["conflict", "disagree", "alignment", "competing"]):
        return "cross-functional disagreement and decision framing"
    if any(term in text for term in ["automation", "workflow", "process", "handoff"]):
        return "process improvement and operational handoff"
    return "the provided case context"


def _interview_role_family(target_role: str, scenario: str) -> str:
    text = f"{target_role} {scenario}".lower()
    if any(term in text for term in ["product marketing", "marketing", "growth", "campaign", "brand", "conversion", "designer"]):
        return "product_marketing"
    if any(term in text for term in ["data analyst", "analytics", "business intelligence", "bi ", "sql", "python", "dashboard"]):
        return "data"
    if any(term in text for term in ["project manager", "project coordinator", "scrum", "agile", "delivery", "timeline"]):
        return "project"
    if any(term in text for term in ["business analyst", "systems analyst", "requirements", "uat", "stakeholder"]):
        return "business"
    return "general"


def _company_context(company: str) -> str:
    company_lower = company.lower()
    if any(term in company_lower for term in ["juice", "cafe", "coffee", "restaurant", "food", "retail"]):
        return "store, loyalty, and customer experience signals"
    if any(term in company_lower for term in ["bank", "credit", "finance", "capital"]):
        return "risk, trust, and customer financial outcomes"
    if any(term in company_lower for term in ["health", "clinic", "hospital", "care"]):
        return "patient experience, compliance, and operational outcomes"
    if any(term in company_lower for term in ["school", "university", "college", "campus"]):
        return "student, staff, and program outcomes"
    if any(term in company_lower for term in ["software", "tech", "saas", "app", "systems"]):
        return "product usage, onboarding, and retention signals"
    return "customer, operational, and business outcomes"


def _question_bank(
    role_family: str,
    target_role: str,
    company: str,
    company_context: str,
    focus: str,
    summary: str,
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    role = target_role.strip() or profile.get("label", "the target role")
    common = [
        {
            "type": "Scenario",
            "question": (
                f"If {company} asked you to tackle {focus}, what clarifying questions would you ask before proposing a solution?"
            ),
            "rubric_focus": "problem framing, stakeholder discovery, assumptions, success criteria",
        },
        {
            "type": "Behavioral",
            "question": (
                f"Tell me about a time you had to turn unclear stakeholder input into a concrete plan or deliverable."
            ),
            "rubric_focus": "STAR structure, stakeholder framing, measurable result",
        },
        {
            "type": "Scenario",
            "question": (
                f"How would you explain your first-week plan for this case: {summary}?"
            ),
            "rubric_focus": "prioritization, risks, evidence, communication plan",
        },
    ]

    if role_family == "product_marketing":
        role_specific = [
            {
                "type": "Technical",
                "question": (
                    f"For {company}, which launch or conversion metrics would you track, and how would you know your work changed customer behavior?"
                ),
                "rubric_focus": "metric selection, customer insight, experiment design, business impact",
            },
            {
                "type": "Scenario",
                "question": (
                    f"Design a practical 30-day plan for improving {company}'s {company_context} while balancing creative quality and measurable growth."
                ),
                "rubric_focus": "audience insight, prioritization, channel strategy, measurable outcomes",
            },
        ]
    elif role_family == "data":
        role_specific = [
            {
                "type": "Technical",
                "question": (
                    f"What data would you pull to investigate {focus}, and how would you validate the result before sharing it with {company}?"
                ),
                "rubric_focus": "data sources, SQL or analysis logic, validation checks, communication",
            },
            {
                "type": "Scenario",
                "question": (
                    f"Which three metrics would you use to brief {company} leadership, and what action could each metric support?"
                ),
                "rubric_focus": "KPI choice, decision relevance, tradeoffs, executive clarity",
            },
        ]
    elif role_family == "project":
        role_specific = [
            {
                "type": "Technical",
                "question": (
                    f"How would you structure the work plan, owners, risks, and checkpoints for {company} if the team had to address {focus}?"
                ),
                "rubric_focus": "scope, owners, timeline, risks, stakeholder communication",
            },
            {
                "type": "Scenario",
                "question": (
                    f"A senior stakeholder at {company} wants faster delivery while the team flags quality concerns. How do you handle the tradeoff?"
                ),
                "rubric_focus": "scope negotiation, escalation, risk mitigation, decision record",
            },
        ]
    elif role_family == "business":
        role_specific = [
            {
                "type": "Technical",
                "question": (
                    f"How would you translate {company}'s case into requirements, acceptance criteria, and metrics the team can build against?"
                ),
                "rubric_focus": "requirements clarity, acceptance criteria, data feasibility, traceability",
            },
            {
                "type": "Scenario",
                "question": (
                    f"Two teams at {company} disagree on what success means for {focus}. How would you lead the working session?"
                ),
                "rubric_focus": "facilitation, prioritization, stakeholder alignment, decision criteria",
            },
        ]
    else:
        role_specific = [
            {
                "type": "Technical",
                "question": (
                    f"As a {role}, what evidence would you gather to make a recommendation for {company}, and how would you measure success?"
                ),
                "rubric_focus": "evidence gathering, metric choice, business reasoning, recommendation quality",
            },
            {
                "type": "Scenario",
                "question": (
                    f"Walk through how you would adapt your approach for {company}'s {company_context} in this situation."
                ),
                "rubric_focus": "context awareness, tradeoffs, stakeholder communication, next steps",
            },
        ]

    return [common[0], *role_specific, common[1], common[2]]


def _dedupe_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for question in questions:
        text = re.sub(r"\s+", " ", question["question"]).strip()
        if text.lower() in seen:
            continue
        seen.add(text.lower())
        question = {**question, "question": text}
        unique.append(question)
    return unique[:5]


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
