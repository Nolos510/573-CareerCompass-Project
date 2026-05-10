from __future__ import annotations

from textwrap import dedent
from typing import Any

from careercompass.state import AgentName, AgentState


SPECIALIST_PROMPT_GOALS: dict[AgentName, str] = {
    "supervisor": "Validate the user request, choose the specialist route, and maintain state.",
    "market_demand": "Extract role-specific skills, tools, qualifications, and evidence from market context.",
    "gap_analysis": "Compare student evidence against market demand and prioritize the missing proof.",
    "curriculum": "Turn skill gaps into a practical 30/60/90-day roadmap with resources and project work.",
    "resume_optimization": "Improve resume language while preserving authentic student experience.",
    "interview_simulation": "Generate and evaluate role-specific practice questions with actionable feedback.",
    "synthesis": "Combine specialist outputs into a coherent career strategy report.",
}


JSON_OUTPUT_GUIDES: dict[AgentName, str] = {
    "market_demand": """
    Return JSON with key "market_skills": [
      {"Skill": "...", "Demand Signal": "Very high|High|Medium|Low", "Evidence": "..."}
    ].
    """,
    "gap_analysis": """
    Return JSON with key "gap_report": [
      {
        "Skill": "...",
        "Current Evidence": "...",
        "Severity": "High|Medium|Low",
        "Recommendation": "...",
        "First Step": "...",
        "Resume Proof": "..."
      }
    ].
    """,
    "curriculum": """
    Return JSON with key "learning_roadmap": [
      {"period": "Days 1-30", "goal": "...", "tasks": ["..."], "resource_relevance": "..."}
    ].
    """,
    "resume_optimization": """
    Return JSON with key "resume_recommendations": [
      {"before": "...", "after": "...", "keywords_added": ["..."]}
    ].
    """,
    "interview_simulation": """
    Return JSON with key "interview_questions": [
      {"type": "Behavioral|Technical|Scenario", "question": "...", "rubric_focus": "..."}
    ].
    """,
    "synthesis": """
    Return JSON with key "final_strategy_report" containing a concise student-facing report.
    """,
    "supervisor": """
    Return JSON with key "route_plan" containing the specialist agents needed for the user intent.
    """,
}


def build_specialist_prompt(agent_name: AgentName, state: AgentState, profile: dict[str, Any]) -> str:
    """Build a compact prompt for a specialist agent.

    The MVP can run without a live LLM, but keeping prompts centralized gives
    TM3 a clear handoff point for OpenAI/Anthropic integration.
    """

    coursework = ", ".join(state.get("coursework", [])[:6]) or "No coursework supplied"
    resume_excerpt = state.get("resume_text", "").strip().replace("\n", " ")[:900]
    if not resume_excerpt:
        resume_excerpt = "No resume text supplied"

    return dedent(
        f"""
        You are the CareerCompass {agent_name.replace('_', ' ').title()}.

        Goal:
        {SPECIALIST_PROMPT_GOALS[agent_name]}

        Student target:
        - Role: {state['target_role']}
        - Location: {state['target_location']}
        - Timeline: {state['timeline_days']} days from hiring target
        - Profile selected: {profile.get('label', 'General career profile')}

        Student evidence:
        - Coursework: {coursework}
        - Resume excerpt: {resume_excerpt}

        Output contract:
        {JSON_OUTPUT_GUIDES[agent_name].strip()}

        Rules:
        - Ground recommendations in the supplied resume, coursework, and market context.
        - Do not invent credentials, employers, certifications, or project outcomes.
        - Prefer specific next steps over generic advice.
        - Preserve the student's voice when suggesting resume edits.
        """
    ).strip()

