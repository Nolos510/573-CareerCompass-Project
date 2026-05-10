from __future__ import annotations

import sys
import time
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

LOCAL_PACKAGES = Path(__file__).resolve().parent / ".packages"
if LOCAL_PACKAGES.exists():
    sys.path.insert(0, str(LOCAL_PACKAGES))

from careercompass.agents import (
    evaluate_interview_answer,
    generate_interview_questions,
    run_career_analysis,
)
from careercompass.demo_data import SAMPLE_COURSEWORK, SAMPLE_RESUME


ACCENT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.stApp {
    background: linear-gradient(145deg, #f8fbfc 0%, #edf7f4 54%, #fff6ed 100%);
    color: #111827;
    font-family: Inter, sans-serif;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #101827 0%, #172033 54%, #0f766e 135%);
}

[data-testid="stSidebar"] * {
    color: #f8fafc;
}

h1 {
    font-weight: 800;
    letter-spacing: 0;
}

h2, h3 {
    letter-spacing: 0;
}

.cc-hero {
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 8px;
    padding: 22px 26px;
    margin: 8px 0 20px 0;
    background: linear-gradient(120deg, rgba(255,255,255,0.92), rgba(240,253,250,0.86));
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
}

.cc-kicker {
    color: #0f766e;
    font-size: 0.82rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 6px;
}

.cc-card {
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 8px;
    padding: 18px;
    background: rgba(255, 255, 255, 0.82);
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
}

div[data-testid="stMetric"] {
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 8px;
    padding: 14px 16px;
    background: rgba(255, 255, 255, 0.86);
    box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
}

.stButton > button,
.stDownloadButton > button {
    border-radius: 8px;
    border: 1px solid rgba(15, 118, 110, 0.18);
    font-weight: 700;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #0f766e, #2563eb);
}

textarea, input {
    border-radius: 8px !important;
}
</style>
"""


COURSEWORK_OPTIONS = [
    "Database Systems",
    "Business Analytics",
    "Project Management",
    "Systems Analysis and Design",
    "Python Programming",
    "Information Security",
    "Operations Management",
]

VIEW_LABELS = {
    "1. Dashboard": "Dashboard",
    "2. Roadmap": "Roadmap",
    "3. Resume": "Resume",
    "4. Interview": "Interview",
    "5. Final Report": "Final Report",
    "6. Action Checklist": "Action Checklist",
}

DEMO_VIEW_PARAMS = {
    "dashboard": "1. Dashboard",
    "roadmap": "2. Roadmap",
    "resume": "3. Resume",
    "interview": "4. Interview",
    "report": "5. Final Report",
    "checklist": "6. Action Checklist",
}


st.set_page_config(
    page_title="CareerCompass",
    page_icon="CC",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_visual_style() -> None:
    st.markdown(ACCENT_CSS, unsafe_allow_html=True)


def initialize_state() -> None:
    defaults = {
        "analysis": None,
        "latency_seconds": None,
        "active_view": "1. Dashboard",
        "last_resume_upload": None,
        "resume_upload_notice": None,
        "resume_text_area": SAMPLE_RESUME,
        "target_role_input": "Business Analyst or Project Manager",
        "target_location_input": "San Francisco Bay Area",
        "timeline_days_input": 90,
        "coursework_input": SAMPLE_COURSEWORK,
        "resume_draft": "",
        "selected_resume_template": "ATS chronological",
        "custom_resume_template": "",
        "practice_questions": None,
        "interview_evaluation": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_demo_profile() -> None:
    st.session_state.analysis = None
    st.session_state.latency_seconds = None
    st.session_state.active_view = "1. Dashboard"
    st.session_state.last_resume_upload = None
    st.session_state.resume_upload_notice = "Sample MIS graduate profile restored."
    st.session_state.resume_text_area = SAMPLE_RESUME
    st.session_state.target_role_input = "Business Analyst or Project Manager"
    st.session_state.target_location_input = "San Francisco Bay Area"
    st.session_state.timeline_days_input = 90
    st.session_state.coursework_input = SAMPLE_COURSEWORK
    st.session_state.resume_draft = ""
    st.session_state.selected_resume_template = "ATS chronological"
    st.session_state.custom_resume_template = ""
    st.session_state.practice_questions = None
    st.session_state.interview_evaluation = None


def sample_demo_inputs() -> dict:
    return {
        "resume_text": SAMPLE_RESUME,
        "target_role": "Business Analyst or Project Manager",
        "target_location": "San Francisco Bay Area",
        "timeline_days": 90,
        "coursework": SAMPLE_COURSEWORK,
    }


def apply_demo_query_params() -> None:
    if st.query_params.get("demo_autorun") != "1":
        return

    view_param = st.query_params.get("demo_view", "dashboard")
    st.session_state.active_view = DEMO_VIEW_PARAMS.get(view_param, "1. Dashboard")

    if st.session_state.get("demo_autorun_view") == view_param and st.session_state.analysis:
        return

    started_at = time.perf_counter()
    st.session_state.analysis = run_career_analysis(sample_demo_inputs())
    st.session_state.latency_seconds = time.perf_counter() - started_at
    st.session_state.practice_questions = None
    st.session_state.interview_evaluation = None
    st.session_state.demo_autorun_view = view_param


def render_demo_cue(title: str, body: str) -> None:
    st.info(f"Presenter cue: {title} - {body}")


def render_sidebar() -> None:
    st.sidebar.title("CareerCompass")
    st.sidebar.caption("Agentic AI career strategy MVP")
    st.sidebar.divider()
    st.sidebar.markdown("**Demo scenario**")
    st.sidebar.write("Recent MIS graduate targeting Business Analyst or Project Manager roles in the Bay Area.")
    st.sidebar.markdown("**5-minute walkthrough**")
    st.sidebar.write("1. Confirm profile")
    st.sidebar.write("2. Run agent workflow")
    st.sidebar.write("3. Explain readiness and gaps")
    st.sidebar.write("4. Show roadmap, resume, and interview outputs")
    st.sidebar.write("5. Close with report, evidence, and advisor disclaimer")
    st.sidebar.divider()
    st.sidebar.markdown("**Agent workflow**")
    st.sidebar.write("Supervisor -> Market -> Gap -> Curriculum -> Resume -> Interview -> Synthesis")


def extract_uploaded_resume(uploaded_file) -> tuple[str | None, str]:
    suffix = uploaded_file.name.lower().rsplit(".", 1)[-1]
    raw = uploaded_file.getvalue()

    if suffix in {"txt", "md"}:
        return raw.decode("utf-8", errors="ignore"), "Resume text loaded from uploaded text file."

    if suffix == "pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            return None, "PDF upload is wired in, but install `pypdf` to extract PDF text."

        reader = PdfReader(uploaded_file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text.strip(), "Resume text extracted from uploaded PDF."

    if suffix == "docx":
        try:
            from docx import Document
        except ImportError:
            return None, "DOCX upload is wired in, but install `python-docx` to extract DOCX text."

        document = Document(uploaded_file)
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        return text.strip(), "Resume text extracted from uploaded DOCX."

    return None, "Unsupported file type. Use TXT, PDF, or DOCX."


def render_inputs() -> dict:
    st.header("Build your career profile")
    st.caption(
        "Paste a resume or upload a local file, then choose the role and hiring-readiness timeline."
    )
    render_demo_cue(
        "Start with the sample student",
        "The defaults match the class demo scenario: MIS graduate, Bay Area, 90-day hiring target.",
    )

    reset_col, note_col = st.columns([0.35, 0.65])
    with reset_col:
        if st.button("Reset sample demo profile"):
            reset_demo_profile()
            st.rerun()
    with note_col:
        st.caption(
            "Use the reset button before recording or presenting so the demo starts from a predictable state."
        )

    left, right = st.columns([1.25, 1])

    with left:
        uploaded_resume = st.file_uploader(
            "Upload resume",
            type=["txt", "md", "pdf", "docx"],
            help="TXT works immediately. PDF and DOCX extraction are supported when optional parser packages are installed.",
        )
        if uploaded_resume and uploaded_resume.name != st.session_state.last_resume_upload:
            extracted_text, notice = extract_uploaded_resume(uploaded_resume)
            st.session_state.last_resume_upload = uploaded_resume.name
            st.session_state.resume_upload_notice = notice
            if extracted_text:
                st.session_state.resume_text_area = extracted_text

        if st.session_state.resume_upload_notice:
            st.info(st.session_state.resume_upload_notice)

        resume_text = st.text_area(
            "Resume text",
            height=300,
            key="resume_text_area",
            help="You can edit uploaded text here before running the analysis.",
        )

    with right:
        target_role = st.text_input(
            "Target role",
            key="target_role_input",
            help="Try Business Analyst, Project Manager, Data Analyst, Product Manager, or a blended target.",
        )
        target_location = st.text_input("Target location", key="target_location_input")
        timeline_days = st.slider(
            "Timeline (days until target hire date)",
            min_value=30,
            max_value=180,
            step=30,
            key="timeline_days_input",
        )
        coursework = st.multiselect(
            "Relevant coursework",
            options=COURSEWORK_OPTIONS,
            key="coursework_input",
        )

    return {
        "resume_text": resume_text,
        "target_role": target_role,
        "target_location": target_location,
        "timeline_days": timeline_days,
        "coursework": coursework,
    }


def render_progress() -> None:
    agents = [
        "Market Demand Agent",
        "Gap Analysis Agent",
        "Curriculum Agent",
        "Resume Optimization Agent",
        "Interview Simulation Agent",
        "Supervisor Synthesis",
    ]

    progress = st.progress(0)
    status = st.empty()

    for index, agent in enumerate(agents, start=1):
        status.write(f"Running {agent}...")
        progress.progress(index / len(agents))
        time.sleep(0.18)

    status.success("Career strategy generated.")


def render_dashboard(analysis: dict) -> None:
    st.header("Career Strategy Dashboard")
    render_demo_cue(
        "Lead with the decision summary",
        "Point to readiness, priority gaps, and next moves before opening the technical trace.",
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Role readiness", f"{analysis['match_percentage']}%")
    c2.metric("Priority gaps", analysis["gap_counts"]["high"])
    c3.metric("Resume keyword coverage", f"{analysis['keyword_coverage']}%")
    c4.metric("Interview readiness", analysis["interview_readiness"])

    st.subheader("Recommended next moves")
    next_actions = pd.DataFrame(analysis["next_actions"])
    st.dataframe(next_actions, use_container_width=True, hide_index=True)

    st.subheader("Market demand summary")
    skills = pd.DataFrame(analysis["market_skills"])
    st.dataframe(skills, use_container_width=True, hide_index=True)

    st.subheader("Skill gap report")
    gaps = pd.DataFrame(analysis["gap_report"])
    st.dataframe(gaps, use_container_width=True, hide_index=True)

    st.subheader("Start closing a gap")
    selected_gap = st.selectbox(
        "Choose a skill gap to work on",
        options=[gap["Skill"] for gap in analysis["gap_report"]],
        help="CareerCompass can turn each recommendation into a first project plan.",
    )
    deep_dive = analysis["gap_deep_dives"][selected_gap]

    with st.container(border=True):
        st.markdown(f"**Why {selected_gap} matters**")
        st.write(deep_dive["why_it_matters"])

        case_col, step_col = st.columns([1, 1])
        with case_col:
            st.markdown("**Starter business cases**")
            for idea in deep_dive["starter_business_cases"]:
                st.checkbox(idea, value=False, key=f"case-{selected_gap}-{idea}")

        with step_col:
            st.markdown("**First steps**")
            for step_number, step in enumerate(deep_dive["first_steps"], start=1):
                st.write(f"{step_number}. {step}")

        st.markdown("**What to research next**")
        st.write(", ".join(deep_dive["search_terms"]))
        st.markdown("**Resume proof to create**")
        st.success(deep_dive["resume_proof"])

    with st.expander("Technical demo notes for the class report"):
        st.write(
            "Latency and evaluation evidence are useful for the project rubric, but less useful as front-and-center student metrics."
        )
        st.metric("End-to-end latency", f"{st.session_state.latency_seconds:.1f}s")
        st.subheader("Supervisor agent trace")
        st.write(" -> ".join(analysis.get("agent_trace", [])))

        handoffs = analysis.get("agent_handoffs", [])
        if handoffs:
            st.subheader("Inter-agent handoffs")
            st.dataframe(pd.DataFrame(handoffs), use_container_width=True, hide_index=True)

        confidence_scores = analysis.get("confidence_scores", {})
        if confidence_scores:
            st.subheader("Confidence scores")
            confidence_rows = [
                {"Signal": key.replace("_", " ").title(), "Score": value}
                for key, value in confidence_scores.items()
            ]
            st.dataframe(pd.DataFrame(confidence_rows), use_container_width=True, hide_index=True)

        st.subheader("Evaluation evidence")
        st.dataframe(
            pd.DataFrame(analysis["evaluation_metrics"]),
            use_container_width=True,
            hide_index=True,
        )


def render_roadmap(analysis: dict) -> None:
    st.header("30/60/90-Day Learning Roadmap")
    render_demo_cue(
        "Show that recommendations become a plan",
        "Each phase turns a skill gap into concrete coursework, practice, and portfolio proof.",
    )
    cols = st.columns(3)
    for col, phase in zip(cols, analysis["learning_roadmap"]):
        with col:
            st.subheader(phase["period"])
            st.write(phase["goal"])
            for task in phase["tasks"]:
                st.checkbox(task, value=False, key=f"{phase['period']}-{task}")
            st.caption(f"Resource relevance: {phase['resource_relevance']}/5")


def render_resume(analysis: dict) -> None:
    st.header("Resume Optimization")
    st.caption("Pick keywords, apply suggested improvements, edit the generated draft, then export.")
    render_demo_cue(
        "Connect market evidence to resume evidence",
        "Show keyword targets first, then demonstrate one before-and-after bullet improvement.",
    )

    st.subheader("Resume keyword targets")
    st.write(
        "These are the words and phrases CareerCompass thinks should be represented somewhere in the resume."
    )
    keyword_df = pd.DataFrame(analysis["keyword_targets"])
    st.dataframe(keyword_df, use_container_width=True, hide_index=True)

    st.subheader("Choose a resume format")
    template_options = list(analysis["resume_templates"].keys()) + ["Use my own template"]
    template_name = st.selectbox(
        "Template",
        options=template_options,
        key="selected_resume_template",
        help="Choose a standard format or paste your own structure.",
    )

    custom_template = ""
    if template_name == "Use my own template":
        custom_template = st.text_area(
            "Paste your template or section order",
            value=st.session_state.custom_resume_template,
            height=180,
            key="custom_resume_template",
            placeholder="Example: Header, Summary, Education, Technical Skills, Projects, Experience, Certifications",
        )
        template = {
            "best_for": "A custom resume structure supplied by the student.",
            "sections": [line.strip() for line in custom_template.splitlines() if line.strip()],
            "preview": build_resume_draft(analysis, custom_template=custom_template),
        }
    else:
        template = analysis["resume_templates"][template_name]

    t1, t2 = st.columns([0.9, 1.1])
    with t1:
        st.markdown(f"**Best for:** {template['best_for']}")
        st.markdown("**Recommended sections**")
        for section in template["sections"] or ["Custom section order will appear here."]:
            st.write(f"- {section}")
    with t2:
        preview = build_resume_draft(analysis, template_name, custom_template)
        st.text_area("Generated template preview", value=preview, height=330)
        if st.button("Save template preview to editable resume"):
            st.session_state.resume_draft = preview
            st.success("Template preview copied into the editable resume draft.")

    st.subheader("Select improvements to apply")
    selected_suggestions = []

    for index, suggestion in enumerate(analysis["resume_recommendations"], start=1):
        with st.container(border=True):
            selected = st.checkbox(
                f"Apply suggestion {index}",
                value=False,
                key=f"resume-suggestion-{index}",
            )
            if selected:
                selected_suggestions.append(suggestion)
            before, after = st.columns(2)
            before.caption("Original")
            before.write(suggestion["before"])
            after.caption("Optimized")
            after.write(suggestion["after"])
            st.caption("Keywords added: " + ", ".join(suggestion["keywords_added"]))

    apply_col, reset_col = st.columns([1, 1])
    with apply_col:
        if st.button("Apply selected suggestions", type="primary"):
            draft = st.session_state.resume_draft or build_resume_draft(
                analysis,
                template_name,
                custom_template,
            )
            st.session_state.resume_draft = apply_resume_suggestions(draft, selected_suggestions)
            st.success("Selected suggestions applied to the editable resume draft.")
    with reset_col:
        if st.button("Reset draft from selected template"):
            st.session_state.resume_draft = build_resume_draft(
                analysis,
                template_name,
                custom_template,
            )

    if not st.session_state.resume_draft:
        st.session_state.resume_draft = build_resume_draft(analysis, template_name, custom_template)

    st.subheader("Editable resume draft")
    st.session_state.resume_draft = st.text_area(
        "Draft resume",
        value=st.session_state.resume_draft,
        height=520,
        help="Edit this directly before exporting.",
    )

    download_col1, download_col2 = st.columns([1, 1])
    with download_col1:
        st.download_button(
            "Export resume as TXT",
            data=st.session_state.resume_draft.encode("utf-8"),
            file_name="careercompass_resume.txt",
            mime="text/plain",
        )
    with download_col2:
        st.download_button(
            "Export resume as DOCX",
            data=build_docx_bytes(st.session_state.resume_draft),
            file_name="careercompass_resume.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )


def render_interview(analysis: dict) -> None:
    st.header("Interview Simulation")
    st.caption(
        "Practice against generated questions, a company-specific scenario, or a scenario the student already received."
    )
    render_demo_cue(
        "Use this as the interactive moment",
        "Generate scenario questions, choose one, and evaluate a short answer to show feedback quality.",
    )

    scenario_options = list(analysis["interview_scenarios"].keys()) + ["Custom scenario"]
    c1, c2 = st.columns([1, 1])
    with c1:
        preset = st.selectbox("Scenario preset", options=scenario_options)
    with c2:
        company = st.text_input("Company or organization", value="Target company")

    default_scenario = (
        ""
        if preset == "Custom scenario"
        else analysis["interview_scenarios"][preset]
    )
    scenario = st.text_area(
        "Scenario details",
        value=default_scenario,
        height=110,
        help="Paste the exact prompt or interview scenario if the company already provided one.",
    )

    if st.button("Generate scenario questions"):
        st.session_state.practice_questions = generate_interview_questions(
            analysis["target_role"],
            company,
            scenario,
        )
        st.session_state.interview_evaluation = None

    questions = st.session_state.practice_questions or analysis["interview_questions"]
    selected_question = st.radio(
        "Choose a question to practice",
        options=[item["question"] for item in questions],
    )

    selected_detail = next(item for item in questions if item["question"] == selected_question)
    st.caption(f"Rubric focus: {selected_detail['rubric_focus']}")

    answer = st.text_area("Your answer", height=180, placeholder="Type a STAR-style answer here...")
    if st.button("Evaluate my answer", type="primary"):
        st.session_state.interview_evaluation = evaluate_interview_answer(
            selected_question,
            answer,
            selected_detail["rubric_focus"],
        )

    if st.session_state.interview_evaluation:
        result = st.session_state.interview_evaluation
        st.subheader("Evaluation")
        st.metric("Practice score", f"{result['score']}/5")
        st.write(result["feedback"])
        with st.expander("Show a strong sample answer"):
            st.write(result["sample_answer"])


def render_report(analysis: dict) -> None:
    st.header("Final Strategy Report")
    render_demo_cue(
        "Close with a copyable deliverable",
        "The final report summarizes the agent outputs and includes the human-advisor review warning.",
    )
    st.text_area("Copyable report", value=analysis["final_strategy_report"], height=360)

    st.warning(
        "CareerCompass recommendations are decision support, not a guarantee. Students should review outputs with a career advisor."
    )


def render_action_checklist(analysis: dict) -> None:
    st.header("Action Checklist")
    st.caption("Use this as a reminder system for missing resume evidence, certifications, and portfolio proof.")
    render_demo_cue(
        "End on actionability",
        "These checkboxes make the strategy feel like a student-facing next-step tracker.",
    )

    st.subheader("Resume evidence reminders")
    for item in analysis["resume_checklist"]:
        st.checkbox(item, value=False, key=f"resume-check-{item}")

    st.subheader("Suggested certifications and short courses")
    st.dataframe(
        pd.DataFrame(analysis["certification_recommendations"]),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Portfolio proof ideas")
    for item in analysis["portfolio_ideas"]:
        st.checkbox(item, value=False, key=f"portfolio-{item}")


def main() -> None:
    apply_visual_style()
    initialize_state()
    apply_demo_query_params()
    render_sidebar()

    st.markdown(
        """
        <div class="cc-hero">
            <div class="cc-kicker">Bay Area career intelligence</div>
            <h1>CareerCompass</h1>
            <p>Personalized career strategy and skill development through coordinated AI agents.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    inputs = render_inputs()

    if st.button("Run CareerCompass analysis", type="primary"):
        started_at = time.perf_counter()
        render_progress()
        st.session_state.analysis = run_career_analysis(inputs)
        st.session_state.latency_seconds = time.perf_counter() - started_at
        st.session_state.practice_questions = None
        st.session_state.interview_evaluation = None
        st.session_state.active_view = "1. Dashboard"

    if st.session_state.analysis:
        views = list(VIEW_LABELS.keys())
        if st.session_state.active_view not in views:
            st.session_state.active_view = "1. Dashboard"
        active_view = st.radio(
            "CareerCompass workspace",
            options=views,
            horizontal=True,
            key="active_view",
        )
        view_name = VIEW_LABELS[active_view]

        if view_name == "Dashboard":
            render_dashboard(st.session_state.analysis)
        elif view_name == "Roadmap":
            render_roadmap(st.session_state.analysis)
        elif view_name == "Resume":
            render_resume(st.session_state.analysis)
        elif view_name == "Interview":
            render_interview(st.session_state.analysis)
        elif view_name == "Final Report":
            render_report(st.session_state.analysis)
        elif view_name == "Action Checklist":
            render_action_checklist(st.session_state.analysis)


def build_resume_draft(
    analysis: dict,
    template_name: str = "ATS chronological",
    custom_template: str = "",
) -> str:
    role = analysis.get("role_label", analysis.get("target_role", "Target Role"))
    keywords = ", ".join(item["Keyword"] for item in analysis["keyword_targets"][:6])
    bullets = "\n".join(
        f"- {item['after']}" for item in analysis["resume_recommendations"]
    )
    certifications = "\n".join(
        f"- {item['Recommendation']} ({item['Priority']})"
        for item in analysis["certification_recommendations"][:4]
    )

    if template_name == "Use my own template" and custom_template.strip():
        return (
            "NAME\n"
            "Email | Phone | LinkedIn | Portfolio\n\n"
            "CUSTOM TEMPLATE STRUCTURE\n"
            f"{custom_template.strip()}\n\n"
            f"TARGET ROLE\n{role}\n\n"
            f"KEYWORD TARGETS\n{keywords}\n\n"
            f"SELECTED EXPERIENCE BULLETS\n{bullets}\n\n"
            f"CERTIFICATIONS TO ADD OR PURSUE\n{certifications}\n"
        )

    if template_name == "Project-forward":
        return (
            "NAME\n"
            "Email | Phone | LinkedIn | Portfolio\n\n"
            f"TARGET ROLE\n{role}\n\n"
            "SELECTED PROJECTS\n"
            "CareerCompass Portfolio Project\n"
            f"{bullets}\n\n"
            f"SKILLS SNAPSHOT\n{keywords}\n\n"
            "EDUCATION\n"
            "B.S. Management Information Systems\n\n"
            f"CERTIFICATIONS\n{certifications}\n"
        )

    if template_name == "Skills matrix":
        return (
            "NAME\n"
            "Email | Phone | LinkedIn | Portfolio\n\n"
            "SUMMARY\n"
            f"Early-career candidate targeting {role} roles with evidence across analysis, tools, projects, and stakeholder communication.\n\n"
            "SKILLS MATRIX\n"
            f"Target Keywords: {keywords}\n"
            "Business Skills: stakeholder communication, requirements, prioritization, recommendations\n"
            "Tools: SQL, dashboards, Excel, project tracking tools\n\n"
            "EVIDENCE BULLETS\n"
            f"{bullets}\n\n"
            "EDUCATION AND CERTIFICATIONS\n"
            "B.S. Management Information Systems\n"
            f"{certifications}\n"
        )

    return (
        "NAME\n"
        "Email | Phone | LinkedIn | Portfolio\n\n"
        "SUMMARY\n"
        f"Early-career {role} candidate with experience in analytics, project work, and stakeholder-focused problem solving. Target keywords include {keywords}.\n\n"
        "EDUCATION\n"
        "B.S. Management Information Systems\n\n"
        "PROJECT EXPERIENCE\n"
        f"{bullets}\n\n"
        "SKILLS\n"
        f"{keywords}\n\n"
        "CERTIFICATIONS\n"
        f"{certifications}\n"
    )


def apply_resume_suggestions(draft: str, suggestions: list[dict]) -> str:
    if not suggestions:
        return draft

    applied_lines = "\n".join(f"- {suggestion['after']}" for suggestion in suggestions)
    return (
        draft.rstrip()
        + "\n\nAPPLIED CAREERCOMPASS IMPROVEMENTS\n"
        + applied_lines
        + "\n"
    )


def build_docx_bytes(text: str) -> bytes:
    try:
        from docx import Document
    except ImportError:
        return text.encode("utf-8")

    document = Document()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            document.add_paragraph("")
        elif line.isupper() and len(line) <= 48:
            document.add_heading(line.title(), level=2)
        elif line.startswith("- "):
            document.add_paragraph(line[2:], style="List Bullet")
        else:
            document.add_paragraph(line)

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


if __name__ == "__main__":
    main()
