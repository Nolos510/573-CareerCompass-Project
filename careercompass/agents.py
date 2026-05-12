from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent
from typing import Any

from careercompass.agent_logic import (
    run_curriculum_logic,
    run_gap_analysis_logic,
    run_interview_evaluation_logic,
    run_interview_question_logic,
    run_market_demand_logic,
    run_resume_optimization_logic,
)
from careercompass.fallbacks import assess_skill_evidence
from careercompass.rag import build_target_job_posting, retrieval_confidence, retrieve_job_postings
from careercompass.state import (
    AgentHandoff,
    AgentName,
    AgentState,
    CareerStrategyOutput,
    WorkflowIntent,
)


OUTPUT_CONTRACT_VERSION = "careercompass.strategy.v1"

REQUIRED_FINAL_OUTPUT_KEYS = {
    "output_contract_version",
    "workflow_intent",
    "route_plan",
    "target_role",
    "target_location",
    "role_label",
    "match_percentage",
    "gap_counts",
    "keyword_coverage",
    "keyword_targets",
    "interview_readiness",
    "market_skills",
    "retrieved_job_postings",
    "gap_report",
    "gap_deep_dives",
    "learning_roadmap",
    "resume_recommendations",
    "resume_templates",
    "interview_questions",
    "interview_scenarios",
    "next_actions",
    "resume_checklist",
    "certification_recommendations",
    "portfolio_ideas",
    "evaluation_metrics",
    "final_strategy_report",
    "agent_trace",
    "agent_handoffs",
    "confidence_scores",
}


@dataclass
class DeterministicCareerWorkflow:
    """LangGraph-compatible fallback for local demos without langgraph installed."""

    def invoke(self, state: AgentState) -> AgentState:
        node_map = {
            "market_demand": market_demand_node,
            "gap_analysis": gap_analysis_node,
            "curriculum": curriculum_node,
            "resume_optimization": resume_optimization_node,
            "interview_simulation": interview_simulation_node,
        }
        state.update(supervisor_node(state))
        for agent_name in state.get("route_plan", []):
            state.update(node_map[agent_name](state))
        state.update(synthesis_node(state))
        return state


def run_career_analysis(inputs: dict) -> CareerStrategyOutput:
    """Run the CareerCompass supervisor workflow.

    The UI-facing output schema stays stable whether LangGraph is installed or
    the local deterministic fallback is used.
    """

    workflow = build_supervisor_workflow()
    final_state = workflow.invoke(create_initial_state(inputs))
    final_output = final_state["final_output"]
    validate_final_output(final_output)
    return final_output


def create_initial_state(inputs: dict) -> AgentState:
    return {
        "user_profile": {
            "resume_supplied": bool(inputs.get("resume_text", "").strip()),
            "coursework_count": len(inputs.get("coursework", [])),
        },
        "target_role": inputs["target_role"],
        "target_location": inputs["target_location"],
        "target_job": _normalize_target_job(inputs.get("target_job")),
        "timeline_days": inputs["timeline_days"],
        "resume_text": inputs.get("resume_text", ""),
        "coursework": inputs.get("coursework", []),
        "retrieved_job_postings": [],
        "market_skills": [],
        "gap_report": [],
        "learning_roadmap": [],
        "resume_recommendations": [],
        "interview_questions": [],
        "interview_feedback": [],
        "confidence_scores": {},
        "final_strategy_report": "",
        "workflow_intent": inputs.get("workflow_intent", "full_strategy"),
        "route_plan": [],
        "completed_agents": [],
        "handoffs": [],
        "errors": [],
    }


def _normalize_target_job(raw_target_job: Any) -> dict[str, str]:
    raw_target_job = raw_target_job if isinstance(raw_target_job, dict) else {}
    return {
        "company": str(raw_target_job.get("company", "")).strip(),
        "title": str(raw_target_job.get("title", "")).strip(),
        "url": str(raw_target_job.get("url", "")).strip(),
        "description": str(raw_target_job.get("description", "")).strip(),
    }


def build_supervisor_workflow():
    """Build a LangGraph StateGraph when available.

    LangGraph is the intended runtime, but the MVP keeps a deterministic local
    fallback so class demos do not fail before dependencies or API keys exist.
    """

    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        return DeterministicCareerWorkflow()

    graph = StateGraph(AgentState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("market_demand", market_demand_node)
    graph.add_node("gap_analysis", gap_analysis_node)
    graph.add_node("curriculum", curriculum_node)
    graph.add_node("resume_optimization", resume_optimization_node)
    graph.add_node("interview_simulation", interview_simulation_node)
    graph.add_node("synthesis", synthesis_node)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_next_agent,
        [
            "market_demand",
            "gap_analysis",
            "curriculum",
            "resume_optimization",
            "interview_simulation",
            "synthesis",
        ],
    )
    for node_name in (
        "market_demand",
        "gap_analysis",
        "curriculum",
        "resume_optimization",
        "interview_simulation",
    ):
        graph.add_conditional_edges(
            node_name,
            route_next_agent,
            [
                "market_demand",
                "gap_analysis",
                "curriculum",
                "resume_optimization",
                "interview_simulation",
                "synthesis",
            ],
        )
    graph.add_edge("synthesis", END)

    return graph.compile()


def supervisor_node(state: AgentState) -> dict[str, Any]:
    profile = _role_profile(state["target_role"])
    route_plan = _route_plan(state.get("workflow_intent", "full_strategy"))
    handoffs = list(state.get("handoffs", []))

    if route_plan:
        handoffs.append(
            _handoff(
                "supervisor",
                route_plan[0],
                "Inputs validated; first specialist agent selected.",
                ["target_role", "target_location", "resume_text", "coursework"],
                _expected_outputs(route_plan[0]),
            )
        )

    return {
        "profile": profile,
        "route_plan": route_plan,
        "handoffs": handoffs,
        "confidence_scores": {
            **state.get("confidence_scores", {}),
            "input_completeness": _input_completeness_score(state),
            "profile_selection": 0.86,
        },
        "completed_agents": _mark_completed(state, "supervisor"),
    }


def market_demand_node(state: AgentState) -> dict[str, Any]:
    profile = _profile_from_state(state)
    retrieved_job_postings = retrieve_job_postings(
        state["target_role"],
        state["target_location"],
    )
    target_posting = build_target_job_posting(
        state.get("target_job"),
        state["target_role"],
        state["target_location"],
    )
    if target_posting:
        retrieved_job_postings = [target_posting, *retrieved_job_postings]
    state_with_retrieval = {
        **state,
        "retrieved_job_postings": retrieved_job_postings,
    }
    market_skills = _market_demand_agent(state_with_retrieval, profile)
    return _agent_update(
        state,
        "market_demand",
        {
            "retrieved_job_postings": retrieved_job_postings,
            "market_skills": market_skills,
        },
        confidence_update={
            "market_data": retrieval_confidence(retrieved_job_postings),
            "retrieval_evidence": retrieval_confidence(retrieved_job_postings),
        },
    )


def gap_analysis_node(state: AgentState) -> dict[str, Any]:
    profile = _profile_from_state(state)
    gap_report = _gap_analysis_agent(state, profile)
    return _agent_update(
        state,
        "gap_analysis",
        {"gap_report": gap_report},
        confidence_update={"gap_analysis": 0.81},
    )


def curriculum_node(state: AgentState) -> dict[str, Any]:
    profile = _profile_from_state(state)
    learning_roadmap = _curriculum_agent(state, profile)
    return _agent_update(
        state,
        "curriculum",
        {"learning_roadmap": learning_roadmap},
        confidence_update={"roadmap_relevance": 0.79},
    )


def resume_optimization_node(state: AgentState) -> dict[str, Any]:
    profile = _profile_from_state(state)
    resume_recommendations = _resume_optimization_agent(state, profile)
    return _agent_update(
        state,
        "resume_optimization",
        {"resume_recommendations": resume_recommendations},
        confidence_update={"resume_keyword_match": profile["keyword_coverage"] / 100},
    )


def interview_simulation_node(state: AgentState) -> dict[str, Any]:
    profile = _profile_from_state(state)
    target_job = state.get("target_job", {})
    company = target_job.get("company") or "Target company"
    scenario = target_job.get("description") or profile["default_interview_scenario"]
    interview_questions = generate_interview_questions(
        state["target_role"],
        company,
        scenario,
    )
    return _agent_update(
        state,
        "interview_simulation",
        {"interview_questions": interview_questions},
        confidence_update={"interview_question_relevance": 0.8},
    )


def synthesis_node(state: AgentState) -> dict[str, Any]:
    profile = _profile_from_state(state)
    high_count = sum(1 for gap in state["gap_report"] if gap["Severity"] == "High")
    keyword_coverage = _keyword_coverage(
        state["market_skills"],
        state["resume_text"],
        state["coursework"],
        profile,
    )
    match_percentage = _match_percentage(keyword_coverage, state["gap_report"])
    final_strategy_report = _synthesis_node(
        state,
        profile,
        state["market_skills"],
        state["gap_report"],
        state["learning_roadmap"],
        state["resume_recommendations"],
        state["interview_questions"],
    )
    completed_agents = _mark_completed(state, "synthesis")
    handoffs = _complete_current_handoffs(state, "synthesis")

    final_output: CareerStrategyOutput = {
        "output_contract_version": OUTPUT_CONTRACT_VERSION,
        "workflow_intent": state.get("workflow_intent", "full_strategy"),
        "route_plan": state.get("route_plan", []),
        "target_role": state["target_role"],
        "target_location": state["target_location"],
        "target_job": state.get("target_job", {}),
        "role_label": profile["label"],
        "match_percentage": match_percentage,
        "gap_counts": {"high": high_count},
        "keyword_coverage": keyword_coverage,
        "keyword_targets": _keyword_targets(profile, state["market_skills"]),
        "interview_readiness": profile["interview_readiness"],
        "market_skills": state["market_skills"],
        "retrieved_job_postings": state["retrieved_job_postings"],
        "gap_report": state["gap_report"],
        "gap_deep_dives": _gap_deep_dives(profile, state["gap_report"]),
        "learning_roadmap": state["learning_roadmap"],
        "resume_recommendations": state["resume_recommendations"],
        "resume_templates": _resume_templates(profile),
        "interview_questions": state["interview_questions"],
        "interview_scenarios": profile["interview_scenarios"],
        "next_actions": _next_actions(profile, state["gap_report"]),
        "resume_checklist": _resume_checklist(profile, state["market_skills"]),
        "certification_recommendations": _certification_recommendations(profile),
        "portfolio_ideas": _portfolio_ideas(profile),
        "evaluation_metrics": _evaluation_metrics(profile),
        "final_strategy_report": final_strategy_report,
        "agent_trace": completed_agents,
        "agent_handoffs": handoffs,
        "confidence_scores": state["confidence_scores"],
    }

    return {
        "final_strategy_report": final_strategy_report,
        "final_output": final_output,
        "completed_agents": completed_agents,
        "handoffs": handoffs,
    }


def validate_final_output(final_output: CareerStrategyOutput) -> None:
    """Assert the cross-agent output contract before the UI consumes it."""

    missing_keys = REQUIRED_FINAL_OUTPUT_KEYS.difference(final_output)
    if missing_keys:
        missing = ", ".join(sorted(missing_keys))
        raise ValueError(f"Final output missing required keys: {missing}")

    if final_output["output_contract_version"] != OUTPUT_CONTRACT_VERSION:
        raise ValueError("Unsupported CareerCompass output contract version.")

    agent_trace = final_output["agent_trace"]
    if not agent_trace or agent_trace[0] != "supervisor" or agent_trace[-1] != "synthesis":
        raise ValueError("Agent trace must begin with supervisor and end with synthesis.")

    queued_handoffs = [
        handoff
        for handoff in final_output["agent_handoffs"]
        if handoff["status"] == "queued"
    ]
    if queued_handoffs:
        raise ValueError("Final output cannot contain queued handoffs.")


def route_next_agent(state: AgentState) -> str:
    completed = set(state.get("completed_agents", []))
    for agent_name in state.get("route_plan", []):
        if agent_name not in completed:
            return agent_name
    return "synthesis"


def _route_plan(intent: WorkflowIntent) -> list[AgentName]:
    plans: dict[WorkflowIntent, list[AgentName]] = {
        "full_strategy": [
            "market_demand",
            "gap_analysis",
            "curriculum",
            "resume_optimization",
            "interview_simulation",
        ],
        "resume_only": ["market_demand", "gap_analysis", "resume_optimization"],
        "interview_only": ["market_demand", "gap_analysis", "interview_simulation"],
    }
    return plans.get(intent, plans["full_strategy"])


def _profile_from_state(state: AgentState) -> dict[str, Any]:
    return state.get("profile") or _role_profile(state["target_role"])


def _agent_update(
    state: AgentState,
    agent_name: AgentName,
    updates: dict[str, Any],
    confidence_update: dict[str, float] | None = None,
) -> dict[str, Any]:
    completed_agents = _mark_completed(state, agent_name)
    handoffs = _complete_current_handoffs(state, agent_name)
    next_agent = _next_planned_agent(state, completed_agents)

    if next_agent:
        handoffs.append(
            _handoff(
                agent_name,
                next_agent,
                f"{agent_name.replace('_', ' ').title()} finished; routing to the next specialist.",
                _required_inputs(next_agent),
                _expected_outputs(next_agent),
            )
        )
    else:
        handoffs.append(
            _handoff(
                agent_name,
                "synthesis",
                "Specialist work complete; supervisor can synthesize the final strategy.",
                [
                    "market_skills",
                    "gap_report",
                    "learning_roadmap",
                    "resume_recommendations",
                    "interview_questions",
                ],
                ["final_strategy_report", "final_output"],
            )
        )

    return {
        **updates,
        "completed_agents": completed_agents,
        "handoffs": handoffs,
        "confidence_scores": {
            **state.get("confidence_scores", {}),
            **(confidence_update or {}),
        },
    }


def _next_planned_agent(
    state: AgentState,
    completed_agents: list[AgentName],
) -> AgentName | None:
    completed = set(completed_agents)
    for agent_name in state.get("route_plan", []):
        if agent_name not in completed:
            return agent_name
    return None


def _mark_completed(state: AgentState, agent_name: AgentName) -> list[AgentName]:
    completed = list(state.get("completed_agents", []))
    if agent_name not in completed:
        completed.append(agent_name)
    return completed


def _complete_current_handoffs(
    state: AgentState,
    agent_name: AgentName,
) -> list[AgentHandoff]:
    handoffs: list[AgentHandoff] = []
    for handoff in state.get("handoffs", []):
        if handoff["to_agent"] == agent_name and handoff["status"] == "queued":
            handoff = {**handoff, "status": "completed"}
        handoffs.append(handoff)
    return handoffs


def _handoff(
    from_agent: AgentName,
    to_agent: AgentName,
    reason: str,
    required_inputs: list[str],
    expected_outputs: list[str],
) -> AgentHandoff:
    return {
        "from_agent": from_agent,
        "to_agent": to_agent,
        "reason": reason,
        "required_inputs": required_inputs,
        "expected_outputs": expected_outputs,
        "status": "queued",
    }


def _required_inputs(agent_name: AgentName) -> list[str]:
    requirements = {
        "market_demand": ["target_role", "target_location"],
        "gap_analysis": ["resume_text", "coursework", "market_skills"],
        "curriculum": ["gap_report", "timeline_days"],
        "resume_optimization": ["resume_text", "gap_report", "market_skills"],
        "interview_simulation": ["target_role", "gap_report"],
        "synthesis": [
            "market_skills",
            "gap_report",
            "learning_roadmap",
            "resume_recommendations",
            "interview_questions",
        ],
    }
    return requirements.get(agent_name, [])


def _expected_outputs(agent_name: AgentName) -> list[str]:
    outputs = {
        "market_demand": ["market_skills", "retrieved_job_postings"],
        "gap_analysis": ["gap_report", "match_percentage"],
        "curriculum": ["learning_roadmap"],
        "resume_optimization": ["resume_recommendations", "keyword_targets"],
        "interview_simulation": ["interview_questions", "interview_feedback"],
        "synthesis": ["final_strategy_report", "final_output"],
    }
    return outputs.get(agent_name, [])


def _input_completeness_score(state: AgentState) -> float:
    signals = [
        bool(state["target_role"].strip()),
        bool(state["target_location"].strip()),
        bool(state["resume_text"].strip()),
        bool(state["coursework"]),
        state["timeline_days"] > 0,
    ]
    return round(sum(signals) / len(signals), 2)


def generate_interview_questions(target_role: str, company: str, scenario: str) -> list[dict]:
    profile = _role_profile(target_role)
    return run_interview_question_logic(target_role, company, scenario, profile)


def evaluate_interview_answer(question: str, answer: str, rubric_focus: str) -> dict:
    return run_interview_evaluation_logic(question, answer, rubric_focus)


def _role_profile(target_role: str) -> dict:
    role = target_role.lower()
    wants_product_marketing = any(
        term in role
        for term in ["product marketing", "growth marketing", "brand", "campaign", "go-to-market", "marketing"]
    )
    wants_ux = any(
        term in role
        for term in ["ux", "user experience", "product design", "designer", "design researcher", "ux research"]
    )
    wants_pm = "project" in role or "program" in role or "manager" in role
    wants_ba = "business analyst" in role or "analyst" in role or "data" in role

    if wants_product_marketing:
        return _product_marketing_profile(target_role)
    if wants_ux:
        return _ux_design_profile(target_role)
    if wants_pm and wants_ba:
        return _hybrid_profile()
    if wants_pm:
        return _project_manager_profile()
    return _business_analyst_profile()


def _product_marketing_profile(target_role: str) -> dict:
    label = target_role.strip() or "Product Marketing Associate"
    return {
        "label": label,
        "match_percentage": 66,
        "keyword_coverage": 58,
        "interview_readiness": "Needs launch stories",
        "skills": [
            ("Product marketing", "Very high", "Core signal for positioning, launch planning, and product-market storytelling."),
            ("customer insight", "Very high", "Employers expect evidence that campaigns and messaging start from customer needs."),
            ("campaign strategy", "High", "Common requirement for channel planning, launch campaigns, and content coordination."),
            ("positioning", "High", "Important for translating product value into clear audience-facing messaging."),
            ("A/B testing", "Medium", "Useful for validating messaging, conversion, and growth experiments."),
        ],
        "gaps": [
            ("Product marketing", "Resume should show launch, messaging, or go-to-market proof.", "High", "Add one truthful launch, campaign, or positioning project."),
            ("customer insight", "Customer research or audience evidence is not yet prominent.", "Medium", "Document one persona, interview, survey, or customer-feedback insight."),
            ("campaign strategy", "Campaign planning evidence could be sharper.", "Medium", "Create a small campaign brief with audience, channels, and success metrics."),
        ],
        "gap_deep_dives": _product_gap_deep_dives(),
        "roadmap": [
            (
                "Days 1-30",
                "Create a product-marketing proof project tied to a real audience.",
                [
                    "Pick one product or local business and define the target customer",
                    "Write a positioning brief with audience, pain point, message, and channel",
                    "Add one resume bullet describing the customer insight and deliverable",
                ],
                5,
            ),
            (
                "Days 31-60",
                "Build measurable campaign and launch evidence.",
                [
                    "Create a launch checklist with channels, content, owners, and metrics",
                    "Draft two campaign variants and define an A/B testing plan",
                    "Package the work as a portfolio case with screenshots and rationale",
                ],
                4,
            ),
            (
                "Days 61-90",
                "Prepare targeted applications and product-marketing interviews.",
                [
                    "Tailor resume bullets to customer insight, positioning, launch, and conversion",
                    "Practice campaign prioritization and metric tradeoff questions",
                    "Apply to product marketing, growth, and marketing associate roles",
                ],
                4,
            ),
        ],
        "technical_question": "How would you decide which launch metrics prove a campaign improved customer behavior?",
        "technical_rubric": "customer insight, metric choice, experiment design, business impact",
        "default_interview_scenario": "a product launch needs clearer positioning and a campaign plan for a specific customer segment",
        "interview_scenarios": {
            "Launch positioning case": (
                "A new product feature is launching next month. The team needs a clear customer segment, positioning, "
                "launch channels, and metrics that show whether the message changed behavior."
            ),
            "Campaign performance review": (
                "A campaign drove traffic but weak conversion. The team needs to understand whether the issue is audience, "
                "message, landing page, channel mix, or product fit."
            ),
            "Customer insight brief": (
                "Sales and support teams report different customer pain points. The interviewer wants to know how you would "
                "gather evidence, synthesize themes, and turn them into messaging."
            ),
            "Creative and metrics tradeoff": (
                "A team likes a bold creative concept, but early data suggests a simpler message converts better. The role "
                "requires balancing creative quality, customer insight, and measurable growth."
            ),
        },
    }


def _ux_design_profile(target_role: str) -> dict:
    label = target_role.strip() or "UX / Product Design"
    return {
        "label": label,
        "match_percentage": 64,
        "keyword_coverage": 56,
        "interview_readiness": "Needs design cases",
        "skills": [
            ("user research", "Very high", "UX roles expect evidence from interviews, surveys, usability findings, or customer discovery."),
            ("product design", "Very high", "Employers look for visible design decisions, interaction flows, and problem framing."),
            ("Figma", "High", "Figma is frequently used to show wireframes, prototypes, and handoff-ready artifacts."),
            ("prototyping", "High", "Prototypes make design thinking visible and testable."),
            ("usability testing", "Medium", "Testing evidence helps prove designs were evaluated with users."),
        ],
        "gaps": [
            ("user research", "Resume should name user evidence, not only design interest.", "High", "Create one user research brief with findings and design implications."),
            ("Figma", "No named Figma or prototyping artifact is visible yet.", "Medium", "Build a small clickable prototype and summarize the design decision."),
            ("usability testing", "Testing evidence could be stronger.", "Medium", "Run a lightweight usability test and document what changed."),
        ],
        "gap_deep_dives": _ux_gap_deep_dives(),
        "roadmap": [
            (
                "Days 1-30",
                "Turn one design problem into a portfolio-ready research story.",
                [
                    "Choose a product flow and write the user problem",
                    "Collect lightweight user feedback or competitive observations",
                    "Create a short findings-to-design-decisions summary",
                ],
                5,
            ),
            (
                "Days 31-60",
                "Create a visible prototype and test plan.",
                [
                    "Build wireframes or a clickable Figma prototype",
                    "Run a usability pass with 2-3 participants or heuristic checks",
                    "Document what changed because of the evidence",
                ],
                4,
            ),
            (
                "Days 61-90",
                "Package the design case for applications and interviews.",
                [
                    "Rewrite resume bullets around research, design decisions, and outcomes",
                    "Practice portfolio walkthroughs and critique responses",
                    "Apply to UX, product design, and UX research-adjacent roles",
                ],
                4,
            ),
        ],
        "technical_question": "How would you validate whether a redesigned onboarding flow actually helped users complete the task?",
        "technical_rubric": "user problem, research method, prototype quality, testing, iteration",
        "default_interview_scenario": "a product onboarding flow has low completion and the team needs research-backed design changes",
        "interview_scenarios": {
            "Onboarding redesign": (
                "A product onboarding flow has low completion. The team needs to understand user friction, redesign the "
                "flow, and explain which evidence would prove the new design is better."
            ),
            "Usability test synthesis": (
                "A usability test produced conflicting feedback. The interviewer wants to know how you would prioritize "
                "issues, identify themes, and decide what to change first."
            ),
            "Stakeholder design critique": (
                "Product, engineering, and marketing disagree on the best design direction. The role needs a clear rationale "
                "that balances user needs, feasibility, and business goals."
            ),
        },
    }


def _product_gap_deep_dives() -> dict[str, Any]:
    return {
        "Product marketing": {
            "why_it_matters": "Product marketing roles need proof that you can connect audience insight to launch and messaging decisions.",
            "starter_business_cases": [
                "Write a launch brief for a small business product or app feature.",
                "Create a positioning comparison for three competitors.",
                "Draft a customer segment and messaging plan for a new feature.",
            ],
            "first_steps": [
                "Pick one target customer and describe their pain point.",
                "Write a one-page positioning brief.",
                "Define launch channels and success metrics.",
                "Turn the brief into one resume bullet and one interview story.",
            ],
            "search_terms": ["product marketing launch brief example", "positioning statement template", "go-to-market portfolio project"],
            "resume_proof": "Add a bullet naming the customer segment, positioning work, launch deliverable, and metric.",
        },
        "customer insight": {
            "why_it_matters": "Customer insight keeps marketing claims grounded in evidence instead of guesses.",
            "starter_business_cases": [
                "Summarize five customer reviews into pain-point themes.",
                "Interview two users and create a persona snapshot.",
                "Compare support tickets against landing-page messaging.",
            ],
            "first_steps": [
                "Choose a small customer data source such as reviews, interviews, or surveys.",
                "Group feedback into 3-4 themes.",
                "Connect each theme to a messaging or product recommendation.",
            ],
            "search_terms": ["customer insight brief example", "voice of customer analysis", "product marketing persona template"],
            "resume_proof": "Add a bullet showing how customer evidence shaped messaging, content, or launch priorities.",
        },
        "campaign strategy": {
            "why_it_matters": "Campaign planning shows you can move from idea to audience, channel, timeline, and measurement.",
            "starter_business_cases": [
                "Plan a two-week campaign for a product feature.",
                "Create three channel-specific messages for one audience.",
                "Define metrics for a launch email, landing page, and social post.",
            ],
            "first_steps": [
                "Choose a campaign objective and target segment.",
                "Map channels, content, owner, timeline, and success metric.",
                "Write one result-oriented resume bullet around the plan.",
            ],
            "search_terms": ["campaign brief template", "product launch campaign example", "marketing metrics beginner guide"],
            "resume_proof": "Add a bullet naming campaign objective, channels, audience, and measurement plan.",
        },
    }


def _ux_gap_deep_dives() -> dict[str, Any]:
    return {
        "user research": {
            "why_it_matters": "UX roles need evidence that design choices came from user problems and observed behavior.",
            "starter_business_cases": [
                "Interview users about a confusing onboarding or checkout flow.",
                "Analyze app reviews to identify usability pain points.",
                "Create a journey map for a student service or small business flow.",
            ],
            "first_steps": [
                "Write the user problem and research question.",
                "Collect 3-5 observations from interviews, reviews, or usability notes.",
                "Summarize findings and connect them to design decisions.",
            ],
            "search_terms": ["UX research brief example", "journey map portfolio project", "user interview synthesis template"],
            "resume_proof": "Add a bullet naming the research method, insight, design implication, and outcome.",
        },
        "Figma": {
            "why_it_matters": "Figma artifacts help employers inspect your design process and handoff readiness.",
            "starter_business_cases": [
                "Redesign one form or dashboard flow in Figma.",
                "Create a clickable prototype for an onboarding improvement.",
                "Document before/after design decisions in a portfolio case.",
            ],
            "first_steps": [
                "Choose one user flow and sketch the current problem.",
                "Build low- and mid-fidelity screens in Figma.",
                "Annotate key design decisions and accessibility considerations.",
            ],
            "search_terms": ["Figma UX portfolio project", "clickable prototype beginner", "UX case study Figma example"],
            "resume_proof": "Add a bullet naming Figma, the flow you prototyped, and the user problem addressed.",
        },
        "usability testing": {
            "why_it_matters": "Testing evidence shows you can improve a design based on feedback instead of preference.",
            "starter_business_cases": [
                "Run a 5-task usability test on a prototype.",
                "Compare task completion before and after a redesign.",
                "Summarize severity and priority for observed usability issues.",
            ],
            "first_steps": [
                "Define 3-5 tasks and success criteria.",
                "Observe users or run a heuristic pass.",
                "Document issues, changes made, and expected impact.",
            ],
            "search_terms": ["usability testing script example", "UX issue severity scale", "prototype testing portfolio case"],
            "resume_proof": "Add a bullet showing test method, finding, design change, and user impact.",
        },
    }


def _business_analyst_profile() -> dict:
    return {
        "label": "Business Analyst",
        "match_percentage": 72,
        "keyword_coverage": 68,
        "interview_readiness": "Developing",
        "skills": [
            ("SQL", "Very high", "Common requirement for querying and joining business data."),
            ("Tableau or Power BI", "High", "Frequently requested for dashboards, KPIs, and reporting."),
            ("Requirements gathering", "Very high", "Repeated expectation for translating business needs into analysis."),
            ("Stakeholder communication", "Very high", "Core skill for presenting insights and recommendations."),
            ("Excel or Python analysis", "Medium", "Useful for ad hoc analysis and automation."),
        ],
        "gaps": [
            ("Tableau or Power BI", "Visualization concepts, but no named dashboard project.", "High", "Create a public dashboard tied to a business case."),
            ("Intermediate SQL", "SQL basics and course registration queries.", "Medium", "Practice joins, CTEs, window functions, and analytics cases."),
            ("Requirements examples", "Coursework mentions projects, but evidence could be sharper.", "Low", "Add one bullet about stakeholder needs and acceptance criteria."),
        ],
        "gap_deep_dives": {
            "Tableau or Power BI": {
                "why_it_matters": "Analyst postings often ask for proof that a candidate can turn messy business data into a dashboard that supports decisions.",
                "starter_business_cases": [
                    "Sales performance dashboard: Which product category should leadership prioritize next quarter?",
                    "Customer churn dashboard: Which customer segment is most at risk and why?",
                    "Campus operations dashboard: Which courses or services are over capacity?",
                ],
                "first_steps": [
                    "Choose one public dataset from Kaggle, data.gov, or a company sample dataset.",
                    "Write a one-sentence business question before opening Tableau or Power BI.",
                    "Build 3-5 visuals: KPI cards, trend line, category comparison, segment breakdown, and recommendation callout.",
                    "Publish the dashboard or export screenshots, then write a short project summary for your resume.",
                ],
                "search_terms": [
                    "Tableau Public sample business dashboard",
                    "Power BI sales dashboard portfolio project",
                    "Kaggle retail sales dataset dashboard",
                ],
                "resume_proof": "Add a bullet naming Tableau or Power BI, the business question, dashboard output, and recommendation.",
            },
            "Intermediate SQL": {
                "why_it_matters": "SQL is the fastest way to show employers that you can retrieve, validate, and explain business data.",
                "starter_business_cases": [
                    "Analyze weekly sales by region and identify the top three drivers of variance.",
                    "Investigate user activity drop-off across acquisition channels.",
                    "Compare course enrollment demand against seat capacity.",
                ],
                "first_steps": [
                    "Pick a dataset with at least three related tables.",
                    "Write queries using joins, aggregations, CTEs, and one window function.",
                    "Save 3-5 queries with comments explaining the business purpose.",
                    "Turn the query output into one chart or short written recommendation.",
                ],
                "search_terms": [
                    "Mode Analytics SQL tutorial",
                    "SQL window functions practice business analyst",
                    "intermediate SQL portfolio project",
                ],
                "resume_proof": "Add a bullet that names the SQL techniques and the decision your analysis supported.",
            },
            "Requirements examples": {
                "why_it_matters": "Business analysts are judged on whether they can clarify vague stakeholder needs into usable requirements.",
                "starter_business_cases": [
                    "A department wants a dashboard but has not defined success metrics.",
                    "A student services team wants to reduce response times.",
                    "A sales team needs a better lead prioritization process.",
                ],
                "first_steps": [
                    "Write five stakeholder questions you would ask.",
                    "Convert answers into must-have and nice-to-have requirements.",
                    "Define acceptance criteria for one deliverable.",
                    "Add the requirements artifact to your project summary.",
                ],
                "search_terms": [
                    "business analyst requirements gathering examples",
                    "acceptance criteria examples business analyst",
                    "user story examples for dashboards",
                ],
                "resume_proof": "Add a bullet that says how you translated stakeholder needs into requirements or acceptance criteria.",
            },
        },
        "roadmap": [
            (
                "Days 1-30",
                "Turn dashboarding from a gap into visible portfolio evidence.",
                [
                    "Complete Tableau Public or Power BI beginner path",
                    "Build one KPI dashboard from a public dataset",
                    "Write a short project summary with business recommendations",
                ],
                5,
            ),
            (
                "Days 31-60",
                "Move SQL from basic to analyst-ready.",
                [
                    "Practice joins, CTEs, and window functions",
                    "Complete 10 analytics SQL problems",
                    "Add SQL project evidence to resume",
                ],
                4,
            ),
            (
                "Days 61-90",
                "Prepare for interviews and targeted applications.",
                [
                    "Rewrite resume bullets for target role",
                    "Practice five STAR interview stories",
                    "Apply to 10 curated Business Analyst roles",
                ],
                4,
            ),
        ],
        "technical_question": "How would you use SQL to investigate a sudden drop in weekly user activity?",
        "technical_rubric": "problem decomposition, joins, aggregation, validation checks",
        "default_interview_scenario": "a dashboard shows revenue is flat while customer acquisition is up",
        "interview_scenarios": {
            "Dashboard performance review": (
                "A weekly executive dashboard shows revenue is flat while customer acquisition is up. "
                "The hiring manager wants to know whether the issue is data quality, conversion, retention, or pricing."
            ),
            "Stakeholder requirements meeting": (
                "A business team asks for a new report but cannot clearly define the audience, decision, success metrics, "
                "or must-have fields. Several stakeholders are using different definitions for the same KPI."
            ),
            "Data quality issue": (
                "Leadership notices two dashboards report different numbers for the same KPI. The source systems, refresh "
                "timing, filters, and ownership are unclear, but the dashboard is used in a monthly operating review."
            ),
            "Process automation handoff": (
                "An operations team wants to automate a manual spreadsheet workflow. They need requirements, exception "
                "handling rules, adoption risks, and a simple way to measure whether the automation saves time."
            ),
            "Executive KPI readout": (
                "A director asks for a short readout explaining why customer support response times improved but customer "
                "satisfaction did not. The analyst must separate noise from likely drivers and recommend next steps."
            ),
            "UAT launch readiness": (
                "A new intake form is scheduled to launch next week. During user acceptance testing, users find confusing "
                "field labels, missing validation, and one report that does not match the agreed acceptance criteria."
            ),
        },
    }


def _project_manager_profile() -> dict:
    return {
        "label": "Project Manager",
        "match_percentage": 69,
        "keyword_coverage": 63,
        "interview_readiness": "Needs scenarios",
        "skills": [
            ("Project planning", "Very high", "Required for scope, timeline, milestones, and delivery tracking."),
            ("Agile / Scrum", "High", "Common in technology and cross-functional project environments."),
            ("Risk management", "High", "Employers expect proactive issue tracking and mitigation planning."),
            ("Jira or Asana", "Medium", "Frequently used for backlog, sprint, and task visibility."),
            ("Stakeholder communication", "Very high", "Core expectation for status updates, escalation, and alignment."),
        ],
        "gaps": [
            ("Agile / Scrum", "Project management coursework exists, but Agile evidence is limited.", "High", "Add Scrum vocabulary and one sprint-style project example."),
            ("Risk management", "Current resume does not show risk tracking or mitigation.", "Medium", "Add a project example with risks, blockers, and escalation."),
            ("Project tooling", "No named tool such as Jira, Asana, Trello, or MS Project.", "Medium", "Complete a short tooling course and build a sample project board."),
        ],
        "gap_deep_dives": {
            "Agile / Scrum": {
                "why_it_matters": "Many entry-level project roles expect candidates to understand sprints, backlog grooming, standups, retrospectives, and prioritization.",
                "starter_business_cases": [
                    "Plan a two-week sprint for launching a student advising dashboard.",
                    "Create a backlog for improving a campus event registration process.",
                    "Run a retrospective for a class project that missed one milestone.",
                ],
                "first_steps": [
                    "Pick a class or personal project and rewrite it as a sprint goal.",
                    "Create backlog items with priority, owner, status, and acceptance criteria.",
                    "Build a simple Jira, Trello, or Asana board.",
                    "Write a resume bullet around sprint planning, blockers, and delivery.",
                ],
                "search_terms": [
                    "Scrum beginner project board example",
                    "Jira fundamentals project manager portfolio",
                    "Agile sprint backlog example",
                ],
                "resume_proof": "Add a bullet naming sprint planning, backlog prioritization, or blocker escalation.",
            },
            "Risk management": {
                "why_it_matters": "Project managers need to show they can anticipate blockers before they become deadline failures.",
                "starter_business_cases": [
                    "A launch date cannot move, but one dependency is delayed.",
                    "A team member becomes unavailable during a critical milestone.",
                    "A stakeholder adds requirements after scope approval.",
                ],
                "first_steps": [
                    "Create a risk register with likelihood, impact, owner, and mitigation.",
                    "Write an escalation plan for the highest risk.",
                    "Draft a stakeholder status update explaining tradeoffs.",
                    "Add the artifact to a portfolio or interview story bank.",
                ],
                "search_terms": [
                    "project risk register template",
                    "project manager escalation plan example",
                    "scope creep interview answer project manager",
                ],
                "resume_proof": "Add a bullet showing risk tracking, escalation, and delivery tradeoffs.",
            },
            "Project tooling": {
                "why_it_matters": "Tools are not the whole job, but they make project coordination visible to employers.",
                "starter_business_cases": [
                    "Track tasks for a dashboard build from requirements to delivery.",
                    "Plan a campus club event with owners, dependencies, and deadlines.",
                    "Create a product launch checklist for a small business.",
                ],
                "first_steps": [
                    "Choose Jira, Asana, Trello, or Microsoft Planner.",
                    "Create at least four columns: backlog, in progress, blocked, done.",
                    "Add owners, due dates, dependencies, and risk labels.",
                    "Screenshot the board and describe the workflow in your resume or portfolio.",
                ],
                "search_terms": [
                    "Jira project management beginner tutorial",
                    "Asana portfolio project example",
                    "Trello project board template",
                ],
                "resume_proof": "Add a bullet naming the tool and how it improved visibility or coordination.",
            },
        },
        "roadmap": [
            (
                "Days 1-30",
                "Translate coursework into project-management evidence.",
                [
                    "Document one class project as scope, timeline, risks, and outcomes",
                    "Create a Jira, Asana, or Trello sample project board",
                    "Rewrite one resume bullet around coordination and delivery",
                ],
                5,
            ),
            (
                "Days 31-60",
                "Build Agile and risk-management credibility.",
                [
                    "Complete Scrum fundamentals",
                    "Practice status reports and escalation messaging",
                    "Create a risk register for a sample project",
                ],
                4,
            ),
            (
                "Days 61-90",
                "Prepare for PM interviews and applications.",
                [
                    "Practice conflict, scope creep, and missed-deadline stories",
                    "Target associate PM, project coordinator, and junior PM roles",
                    "Add certification progress to resume",
                ],
                4,
            ),
        ],
        "technical_question": "How would you recover a project that is two weeks behind schedule with a fixed launch date?",
        "technical_rubric": "scope tradeoffs, stakeholder communication, risk mitigation, prioritization",
        "default_interview_scenario": "a cross-functional project is behind schedule and stakeholders disagree on what to cut",
        "interview_scenarios": {
            "Scope creep": (
                "Stakeholders keep adding requirements after the project timeline has already been approved. The team can "
                "absorb only some changes without risking launch quality or the committed deadline."
            ),
            "Missed deadline": (
                "A cross-functional project is two weeks behind schedule and stakeholders disagree on what to cut. "
                "The sponsor wants a recovery plan with tradeoffs, risks, owners, and a new checkpoint cadence."
            ),
            "Team conflict": (
                "Engineering and business teams disagree about whether a feature is ready to launch. One side is worried "
                "about defects while the other is worried about missing a promised customer milestone."
            ),
            "Vendor migration risk": (
                "A vendor tool migration is approaching go-live, but data mapping, training, and rollback plans are not "
                "fully resolved. Leaders need a decision on whether to launch, delay, or reduce scope."
            ),
            "Resource constraint": (
                "Two priority projects need the same designer and analyst during the same sprint. Each sponsor claims "
                "their work is urgent, and the project manager must create a transparent prioritization path."
            ),
            "Executive escalation": (
                "A project dependency is blocked by another department. The team has tried informal follow-ups, but the "
                "launch date is at risk and executives need a concise escalation with options."
            ),
        },
    }


def _hybrid_profile() -> dict:
    base = _business_analyst_profile()
    pm = _project_manager_profile()
    return {
        **base,
        "label": "Business Analyst / Project Manager",
        "match_percentage": 70,
        "keyword_coverage": 65,
        "interview_readiness": "Developing",
        "skills": base["skills"][:3] + pm["skills"][:3],
        "gaps": [
            base["gaps"][0],
            pm["gaps"][0],
            ("Project-to-analysis storytelling", "Resume lists projects but does not connect analysis to delivery outcomes.", "Medium", "Frame one project as requirements, analysis, decision, and delivery impact."),
        ],
        "gap_deep_dives": {
            **base["gap_deep_dives"],
            **pm["gap_deep_dives"],
            "Project-to-analysis storytelling": {
                "why_it_matters": "Hybrid BA/PM roles reward candidates who can connect analysis work to coordination, prioritization, and delivery outcomes.",
                "starter_business_cases": [
                    "Build a dashboard and project plan for improving a support-ticket process.",
                    "Analyze event registration data and coordinate a process improvement rollout.",
                    "Create a KPI dashboard plus a stakeholder implementation plan.",
                ],
                "first_steps": [
                    "Pick one business problem and define both the analysis output and project deliverable.",
                    "Write requirements, dashboard metrics, timeline, risks, and final recommendation.",
                    "Create a simple dashboard or tracker as proof.",
                    "Write two resume bullets: one analyst-heavy and one PM-heavy.",
                ],
                "search_terms": [
                    "business analyst project manager portfolio example",
                    "dashboard requirements project plan example",
                    "hybrid BA PM resume bullet examples",
                ],
                "resume_proof": "Frame the same project as requirements, analysis, stakeholder alignment, and delivery impact.",
            },
        },
        "roadmap": [
            (
                "Days 1-30",
                "Create one portfolio project that shows analysis and project coordination.",
                [
                    "Build a dashboard or planning tracker around a business problem",
                    "Document requirements, timeline, risks, and final recommendation",
                    "Add one hybrid resume bullet showing both analysis and coordination",
                ],
                5,
            ),
            (
                "Days 31-60",
                "Strengthen SQL, dashboarding, and Agile evidence.",
                [
                    "Practice intermediate SQL cases",
                    "Complete a Scrum fundamentals module",
                    "Create a project board for the portfolio case",
                ],
                4,
            ),
            (
                "Days 61-90",
                "Practice hybrid BA/PM interviews and apply selectively.",
                [
                    "Practice stakeholder, prioritization, and metric-case questions",
                    "Target BA, project coordinator, and associate PM roles",
                    "Finalize resume variants for analyst-heavy and PM-heavy roles",
                ],
                4,
            ),
        ],
        "technical_question": "How would you prioritize dashboard requirements when stakeholders want more metrics than the project timeline allows?",
        "technical_rubric": "requirements triage, stakeholder alignment, data feasibility, delivery tradeoffs",
        "default_interview_scenario": "stakeholders want a dashboard and project plan, but disagree on which metrics matter most",
        "interview_scenarios": {
            "Hybrid BA/PM case": (
                "Stakeholders want a dashboard and project plan, but disagree on which metrics matter most. The team needs "
                "requirements, a delivery timeline, and a decision framework for what will be included in the first release."
            ),
            "Prioritization conflict": (
                "Two teams request different deliverables and both claim their request is urgent. The candidate must compare "
                "business value, effort, dependencies, risks, and the evidence behind each request."
            ),
            "Data and delivery issue": (
                "The project is on schedule, but the underlying data has quality problems. Leaders still expect a launch "
                "update, so the team must decide what can be shipped, what needs caveats, and who owns remediation."
            ),
            "Automation rollout": (
                "A manual approval workflow is being replaced with a lightweight automation. Users are worried about edge "
                "cases, managers want cycle-time reporting, and the project needs rollout training."
            ),
            "Metrics definition workshop": (
                "Sales, operations, and support leaders each define active customer differently. The interview case asks how "
                "to facilitate alignment, document the definition, and build a dashboard everyone trusts."
            ),
            "Launch retrospective": (
                "A launch hit the date but missed adoption goals. The team needs to analyze what happened, separate delivery "
                "issues from market-fit issues, and create a practical improvement plan."
            ),
        },
    }


def _market_demand_agent(inputs: dict, profile: dict) -> list[dict]:
    return run_market_demand_logic(inputs, profile)


def _gap_analysis_agent(inputs: dict, profile: dict) -> list[dict]:
    return run_gap_analysis_logic(inputs, profile)


def _curriculum_agent(inputs: dict, profile: dict) -> list[dict]:
    return run_curriculum_logic(inputs, profile)


def _resume_optimization_agent(inputs: dict, profile: dict) -> list[dict]:
    return run_resume_optimization_logic(inputs, profile)


def _keyword_coverage(
    market_skills: list[dict],
    resume_text: str,
    coursework: list[str],
    profile: dict,
) -> int:
    if not market_skills:
        return profile["keyword_coverage"]

    checked_skills = market_skills[:8]
    coverage_score = sum(
        _evidence_credit(
            assess_skill_evidence(skill["Skill"], resume_text, coursework)["status"]
        )
        for skill in checked_skills
    )
    return round((coverage_score / max(len(checked_skills), 1)) * 100)


def _evidence_credit(status: str) -> float:
    if status == "Strong Evidence":
        return 1.0
    if status == "Mentioned":
        return 0.5
    return 0.0


def _match_percentage(keyword_coverage: int, gap_report: list[dict]) -> int:
    if not gap_report:
        return max(50, keyword_coverage)

    high_gaps = sum(1 for gap in gap_report if gap["Severity"] == "High")
    medium_gaps = sum(1 for gap in gap_report if gap["Severity"] == "Medium")
    gap_penalty = high_gaps * 9 + medium_gaps * 5
    score = 52 + round(keyword_coverage * 0.45) - gap_penalty
    return max(25, min(92, score))


def _gap_deep_dives(profile: dict, gap_report: list[dict]) -> dict[str, Any]:
    deep_dives = dict(profile["gap_deep_dives"])
    for gap in gap_report:
        skill = gap["Skill"]
        if skill in deep_dives:
            continue
        deep_dives[skill] = {
            "why_it_matters": (
                f"{skill} appears in the retrieved market evidence for this role target, "
                "so CareerCompass treats it as a practical proof point for applications."
            ),
            "starter_business_cases": [
                f"Use {skill} in a small portfolio case tied to the target role.",
                f"Rework one class project to make {skill} visible.",
                f"Create a one-page project summary that names {skill} and the business outcome.",
            ],
            "first_steps": [
                gap["First Step"],
                "Document the context, deliverable, and result in plain language.",
                "Turn the work into one resume bullet and one interview story.",
            ],
            "search_terms": [
                f"{skill} beginner portfolio project",
                f"{skill} resume bullet examples",
                f"{skill} {profile['label']} interview question",
            ],
            "resume_proof": gap["Resume Proof"],
        }
    return deep_dives


def _keyword_targets(profile: dict, market_skills: list[dict] | None = None) -> list[dict]:
    if market_skills:
        return [
            {
                "Keyword": skill["Skill"],
                "Priority": "High" if skill["Demand Signal"] in {"Very high", "High"} else "Medium",
                "Where to use it": "Skills, project bullets, and portfolio evidence",
                "Why": skill["Evidence"],
            }
            for skill in market_skills[:8]
        ]

    if "Project Manager" in profile["label"] and "Business Analyst" not in profile["label"]:
        return [
            {"Keyword": "scope", "Priority": "High", "Where to use it": "Project bullets and summary", "Why": "Shows control of project boundaries."},
            {"Keyword": "milestones", "Priority": "High", "Where to use it": "Project coordination bullets", "Why": "Signals timeline ownership."},
            {"Keyword": "risk management", "Priority": "High", "Where to use it": "Project experience", "Why": "Important for PM credibility."},
            {"Keyword": "stakeholder communication", "Priority": "High", "Where to use it": "Summary and experience", "Why": "Core PM hiring signal."},
            {"Keyword": "Agile", "Priority": "Medium", "Where to use it": "Skills and certification areas", "Why": "Common technology PM requirement."},
            {"Keyword": "Jira", "Priority": "Medium", "Where to use it": "Tools section", "Why": "Common PM execution tool."},
        ]

    targets = [
        {"Keyword": "SQL", "Priority": "High", "Where to use it": "Skills and project bullets", "Why": "Core analyst screening keyword."},
        {"Keyword": "Tableau", "Priority": "High", "Where to use it": "Skills, projects, portfolio", "Why": "Directly supports dashboard and BI roles."},
        {"Keyword": "Power BI", "Priority": "High", "Where to use it": "Skills or project alternative to Tableau", "Why": "Common BI keyword in job posts."},
        {"Keyword": "KPIs", "Priority": "High", "Where to use it": "Dashboard bullets", "Why": "Connects analysis to business measurement."},
        {"Keyword": "requirements gathering", "Priority": "Medium", "Where to use it": "Project or experience bullets", "Why": "Business analyst role signal."},
        {"Keyword": "stakeholder recommendations", "Priority": "Medium", "Where to use it": "Summary and project bullets", "Why": "Shows communication and decision support."},
    ]
    if "Project Manager" in profile["label"]:
        targets.extend(
            [
                {"Keyword": "Agile", "Priority": "High", "Where to use it": "Skills and project bullets", "Why": "Supports the PM side of the hybrid role."},
                {"Keyword": "project coordination", "Priority": "High", "Where to use it": "Experience bullets", "Why": "Shows delivery and ownership."},
            ]
        )
    return targets


def _resume_templates(profile: dict) -> dict:
    skills = [skill for skill, _demand, _evidence in profile["skills"][:5]]
    role = profile["label"]
    return {
        "ATS chronological": {
            "best_for": "Most job applications and applicant tracking systems.",
            "sections": [
                "Header: name, email, phone, LinkedIn, portfolio",
                "Summary: 2-3 lines tailored to the target role",
                "Education",
                "Projects or experience in reverse chronological order",
                "Skills grouped by tools, analysis, and business/process",
                "Certifications",
            ],
            "preview": dedent(
                f"""
                NAME
                Email | Phone | LinkedIn | Portfolio

                SUMMARY
                Early-career {role} candidate with experience in coursework, projects, and stakeholder-focused problem solving. Skilled in {', '.join(skills[:3])}.

                EDUCATION
                B.S. Management Information Systems

                PROJECT EXPERIENCE
                Project Name | Course or Organization | Date
                - Built or coordinated [deliverable] using [tools] to support [business decision].
                - Communicated findings, risks, or requirements to [stakeholder group].

                SKILLS
                Tools: {', '.join(skills[:4])}
                Business: stakeholder communication, requirements, prioritization

                CERTIFICATIONS
                Certification name, in progress or completed
                """
            ).strip(),
        },
        "Project-forward": {
            "best_for": "Students with strong class, portfolio, or capstone projects but limited formal experience.",
            "sections": [
                "Header",
                "Targeted summary",
                "Selected projects",
                "Technical and business skills",
                "Education",
                "Certifications and coursework",
            ],
            "preview": dedent(
                f"""
                NAME
                Email | Phone | LinkedIn | Portfolio

                TARGET ROLE: {role}

                SELECTED PROJECTS
                Business Case Project
                - Problem: [business question or project challenge].
                - Action: [analysis, dashboard, project plan, requirements, or coordination].
                - Result: [recommendation, measured improvement, or decision supported].

                SKILLS SNAPSHOT
                {', '.join(skills)}

                EDUCATION AND COURSEWORK
                MIS coursework: databases, analytics, project management, systems analysis
                """
            ).strip(),
        },
        "Skills matrix": {
            "best_for": "Career pivots where the student needs to make transferable skills obvious.",
            "sections": [
                "Header",
                "Professional summary",
                "Skills matrix",
                "Evidence bullets under each skill group",
                "Experience/projects",
                "Education and certifications",
            ],
            "preview": dedent(
                f"""
                NAME
                Email | Phone | LinkedIn | Portfolio

                SUMMARY
                Candidate targeting {role} roles with a mix of technical, analytical, and coordination experience.

                SKILLS MATRIX
                Analysis / Delivery: {', '.join(skills[:3])}
                Communication: stakeholder updates, requirements, presentations
                Tools: Excel, SQL, dashboards, project tracking tools

                EVIDENCE
                - Analysis: [project showing data-to-decision work].
                - Delivery: [project showing timeline, coordination, or risk management].
                - Communication: [presentation or stakeholder-facing artifact].
                """
            ).strip(),
        },
    }


def _next_actions(profile: dict, gap_report: list[dict] | None = None) -> list[dict]:
    if gap_report:
        first_gap = gap_report[0]
        first_action = first_gap["Recommendation"]
        first_skill = first_gap["Skill"]
    else:
        profile_gap = profile["gaps"][0]
        first_action = profile_gap[3]
        first_skill = profile_gap[0]

    return [
        {"Priority": "This week", "Action": first_action, "Why it matters": f"Addresses {first_skill}, your highest-priority gap."},
        {"Priority": "Next 30 days", "Action": profile["roadmap"][0][2][0], "Why it matters": "Turns coursework into visible proof."},
        {"Priority": "Before applying", "Action": "Add certification progress or portfolio evidence to the resume.", "Why it matters": "Recruiters need quick proof, not hidden capability."},
    ]


def _resume_checklist(profile: dict, market_skills: list[dict] | None = None) -> list[str]:
    tool_examples = ", ".join(skill["Skill"] for skill in (market_skills or [])[:5])
    if not tool_examples:
        tool_examples = "SQL, Tableau, Jira, Python, Excel, or SAP"

    return [
        "Have you added relevant certifications or in-progress certifications?",
        f"Have you named the tools you actually used, such as {tool_examples}?",
        "Have you included a measurable result, business impact, or stakeholder outcome?",
        "Have you added one portfolio project link or short project summary?",
        f"Have you customized at least three bullets for {profile['label']} roles?",
    ]


def _certification_recommendations(profile: dict) -> list[dict]:
    profile_label = profile["label"].lower()
    if "marketing" in profile_label:
        return [
            {"Area": "Product marketing", "Recommendation": "Product Marketing Alliance Core certification or free PMM fundamentals", "Priority": "High", "Why": "Builds vocabulary for positioning, launch, and GTM interviews."},
            {"Area": "Customer insight", "Recommendation": "HubSpot customer research and buyer persona modules", "Priority": "High", "Why": "Supports audience and persona evidence."},
            {"Area": "Growth", "Recommendation": "Google Analytics or experimentation basics", "Priority": "Medium", "Why": "Helps connect campaigns to conversion and behavior metrics."},
            {"Area": "Portfolio", "Recommendation": "Create one launch brief and campaign case study", "Priority": "High", "Why": "Employers need visible proof of launch thinking."},
        ]

    if "ux" in profile_label or "design" in profile_label:
        return [
            {"Area": "UX research", "Recommendation": "Google UX Design Certificate research and testing modules", "Priority": "High", "Why": "Provides structured evidence for research, prototypes, and testing."},
            {"Area": "Figma", "Recommendation": "Figma Learn: prototyping and design systems", "Priority": "High", "Why": "Supports portfolio-ready design artifacts."},
            {"Area": "Accessibility", "Recommendation": "Deque University free accessibility basics or WCAG intro", "Priority": "Medium", "Why": "Adds practical design quality language."},
            {"Area": "Portfolio", "Recommendation": "Create one UX case study with research, prototype, and testing notes", "Priority": "High", "Why": "Hiring teams need a walkthrough-ready project."},
        ]

    if "Project Manager" in profile["label"] and "Business Analyst" not in profile["label"]:
        return [
            {"Area": "Project management", "Recommendation": "Google Project Management Certificate", "Priority": "High", "Why": "Beginner-friendly PM proof for entry-level roles."},
            {"Area": "Agile", "Recommendation": "Scrum.org Professional Scrum Master I overview", "Priority": "High", "Why": "Adds Scrum vocabulary and interview examples."},
            {"Area": "Tooling", "Recommendation": "Atlassian Jira Fundamentals", "Priority": "Medium", "Why": "Shows familiarity with common PM tooling."},
            {"Area": "PM foundation", "Recommendation": "PMI CAPM", "Priority": "Medium", "Why": "Recognized certification for early-career project roles."},
        ]

    recommendations = [
        {"Area": "Analytics", "Recommendation": "IBM Data Analyst Professional Certificate", "Priority": "High", "Why": "Signals SQL, spreadsheets, dashboards, and analysis workflow."},
        {"Area": "Visualization", "Recommendation": "Tableau Desktop Specialist or Tableau Public portfolio", "Priority": "High", "Why": "Directly addresses dashboarding gaps."},
        {"Area": "Business intelligence", "Recommendation": "Microsoft PL-300 Power BI learning path", "Priority": "Medium", "Why": "Useful alternative to Tableau in many analyst roles."},
        {"Area": "Data/AI", "Recommendation": "NVIDIA Deep Learning Institute beginner course", "Priority": "Optional", "Why": "Helpful if targeting AI-enabled analytics roles."},
        {"Area": "Enterprise systems", "Recommendation": "SAP learning journey or SAP TS410 overview", "Priority": "Optional", "Why": "Relevant for ERP, operations, and enterprise analyst paths."},
    ]

    if "Project Manager" in profile["label"]:
        recommendations.insert(
            2,
            {"Area": "Agile", "Recommendation": "Scrum fundamentals or Jira Fundamentals", "Priority": "High", "Why": "Supports the project-management side of a hybrid BA/PM target."},
        )
    return recommendations


def _portfolio_ideas(profile: dict) -> list[str]:
    profile_label = profile["label"].lower()
    if "marketing" in profile_label:
        return [
            "Create a product launch brief with audience, positioning, channels, and metrics.",
            "Build a campaign plan with two message variants and an experiment hypothesis.",
            "Write a one-page customer insight summary from reviews, interviews, or survey data.",
        ]

    if "ux" in profile_label or "design" in profile_label:
        return [
            "Create a UX case study showing problem, research, prototype, and iteration.",
            "Build a clickable Figma prototype for one improved user flow.",
            "Run a lightweight usability test and document before/after design changes.",
        ]

    if "Project Manager" in profile["label"] and "Business Analyst" not in profile["label"]:
        return [
            "Create a sample project charter with scope, timeline, stakeholders, and risks.",
            "Build a Jira, Trello, or Asana board for a realistic project case.",
            "Write a one-page retrospective explaining blockers, tradeoffs, and lessons learned.",
        ]

    return [
        "Publish a Tableau or Power BI dashboard using a public dataset.",
        "Write a short SQL case study explaining the business question, query approach, and recommendation.",
        "Create a one-page requirements brief that connects stakeholder needs to dashboard metrics.",
    ]


def _evaluation_metrics(profile: dict) -> list[dict]:
    return [
        {
            "Metric": "End-to-end latency",
            "Target": "Under 30 seconds",
            "Current MVP Evidence": "Stubbed demo path runs under target locally.",
        },
        {
            "Metric": "Skill gap accuracy",
            "Target": "80 percent manual agreement",
            "Current MVP Evidence": f"To be tested against sample {profile['label']} postings.",
        },
        {
            "Metric": "Resume keyword coverage",
            "Target": "Improved keyword coverage",
            "Current MVP Evidence": f"Demo estimates {profile['keyword_coverage']} percent coverage after recommendations.",
        },
        {
            "Metric": "Interview relevance",
            "Target": "4 out of 5 average rating",
            "Current MVP Evidence": f"Questions align to {profile['label']} responsibilities.",
        },
        {
            "Metric": "Ethics controls",
            "Target": "Privacy, bias, and overconfidence mitigations documented",
            "Current MVP Evidence": "Final report includes confidence and advisor review warning.",
        },
    ]


def _sample_answer(question: str, rubric_focus: str) -> str:
    return (
        "In a class analytics project, my team had unclear stakeholder expectations for what the final dashboard should show. "
        "I clarified the business question, grouped requirements into must-have and nice-to-have metrics, and built a simple "
        "analysis plan before creating the final deliverable. I then presented the recommendation in terms of decision impact, "
        "not just charts. The result was a clearer final presentation and a dashboard that connected the data work to a specific "
        f"business decision. This answer works because it addresses {rubric_focus}."
    )


def _synthesis_node(
    inputs: dict,
    profile: dict,
    market_skills: list[dict],
    gap_report: list[dict],
    learning_roadmap: list[dict],
    resume_recommendations: list[dict],
    interview_questions: list[dict],
) -> str:
    role = inputs["target_role"]
    location = inputs["target_location"]
    target_job = inputs.get("target_job", {})
    target_job_label = ""
    if target_job.get("title") or target_job.get("company"):
        target_job_label = f"\n        Target job: {target_job.get('title') or role}"
        if target_job.get("company"):
            target_job_label += f" at {target_job['company']}"
    timeline = inputs["timeline_days"]
    readiness = _match_percentage(
        _keyword_coverage(
            market_skills,
            inputs.get("resume_text", ""),
            inputs.get("coursework", []),
            profile,
        ),
        gap_report,
    )
    top_skills = ", ".join(skill["Skill"] for skill in market_skills[:4])
    gaps = "\n".join(
        f"{index}. {gap['Skill']} - {gap['Severity']} severity. {gap['Recommendation']}"
        for index, gap in enumerate(gap_report, start=1)
    )
    roadmap = "\n".join(
        f"{phase['period']}: {phase['goal']}"
        for phase in learning_roadmap
    )

    return dedent(
        f"""
        CareerCompass Strategy Report

        Target: {role} in {location}
        {target_job_label}
        Timeline: {timeline} days until target hire date
        Estimated readiness: {readiness} percent match

        Market Demand Summary
        The strongest demand signals for this target are {top_skills}. These should guide the student's resume, learning roadmap, and interview preparation.

        Priority Skill Gaps
        {gaps}

        30/60/90-Day Roadmap
        {roadmap}

        Resume Strategy
        Improve bullets by naming tools, outcomes, measurable impact, and stakeholder value. Preserve the student's actual experience and avoid exaggerated claims.

        Interview Strategy
        Practice role-specific scenarios using STAR structure, clear tradeoffs, and measurable results. Use the interview simulator to generate company-specific questions.

        Ethical Safeguard
        This report is decision support. Recommendations should be reviewed with a career advisor, and resume data should not be stored beyond the active session.
        """
    ).strip()
