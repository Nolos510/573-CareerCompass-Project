from __future__ import annotations

import re
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
from careercompass.fallbacks import assess_skill_evidence
from careercompass.rag import (
    available_coursework_options,
    available_locations,
    available_target_roles,
)


ACCENT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.stApp {
    background:
        radial-gradient(circle at 12% 8%, rgba(20, 184, 166, 0.16), transparent 28%),
        radial-gradient(circle at 86% 10%, rgba(249, 115, 22, 0.14), transparent 26%),
        linear-gradient(145deg, #f7fbff 0%, #eef6f5 48%, #fff8f1 100%);
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
    border-radius: 18px;
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

.cc-status-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 10px;
    margin: 10px 0 18px 0;
}

.cc-status {
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 8px;
    padding: 12px;
    background: rgba(255, 255, 255, 0.78);
    min-height: 112px;
}

.cc-status strong {
    display: block;
    font-size: 0.9rem;
    margin-bottom: 4px;
}

.cc-status span {
    display: inline-block;
    color: #0f766e;
    font-size: 0.74rem;
    font-weight: 800;
    margin-bottom: 8px;
    text-transform: uppercase;
}

.cc-status p {
    font-size: 0.82rem;
    line-height: 1.35;
    margin: 0;
}

.cc-demo-cue {
    border-left: 5px solid #0f766e;
    border-radius: 8px;
    padding: 14px 16px;
    background: rgba(240, 253, 250, 0.9);
    margin: 8px 0 18px 0;
}

.cc-demo-cue strong {
    color: #0f766e;
}

@media (max-width: 1100px) {
    .cc-status-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
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
    border-radius: 12px;
    border: 1px solid rgba(15, 118, 110, 0.18);
    font-weight: 700;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #0f766e, #2563eb);
}

textarea, input {
    border-radius: 12px !important;
}
</style>
"""


ROLE_STATUS = [
    {
        "owner": "Carlo",
        "lane": "Architecture",
        "status": "In progress",
        "summary": "Supervisor workflow, shared state, inter-agent handoffs, and UI integration are wired.",
    },
    {
        "owner": "Nhi",
        "lane": "RAG/Data",
        "status": "Started",
        "summary": "Local job-posting evidence and retrieval scoring now feed the Market Demand Agent.",
    },
    {
        "owner": "TM3",
        "lane": "Agent Logic",
        "status": "Started",
        "summary": "Prompts, JSON contracts, validation, OpenAI hook, and fallbacks are scaffolded.",
    },
    {
        "owner": "TM4",
        "lane": "Frontend/Demo",
        "status": "Active now",
        "summary": "Streamlit presenter flow, demo script, and screenshot checklist are being prepared.",
    },
    {
        "owner": "TM5",
        "lane": "Evaluation/Deployment",
        "status": "Started",
        "summary": "Docker, evaluation plan, ethics notes, and deployment docs are now scaffolded.",
    },
]


DEMO_CUES = {
    "Dashboard": "Lead with the value proposition: CareerCompass turns a resume, coursework, and a target role into a coordinated career strategy.",
    "Roadmap": "Explain that recommendations become a time-bound learning plan, not generic advice.",
    "Resume": "Show keyword targets, selectable improvements, editable draft, and DOCX export.",
    "Interview": "Use Salesforce or another Bay Area company, generate scenario questions, answer one, then show scoring and sample answer.",
    "Final Report": "Call out that the supervisor synthesizes every specialist output into one student-facing strategy report.",
    "Action Checklist": "Close with practical next steps: certifications, missing evidence, and portfolio proof.",
}

DEMO_VIEW_PARAMS = {
    "dashboard": "Dashboard",
    "roadmap": "Roadmap",
    "resume": "Resume",
    "interview": "Interview",
    "report": "Final Report",
    "checklist": "Action Checklist",
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
        "active_view": "Dashboard",
        "last_resume_upload": None,
        "resume_upload_notice": None,
        "resume_text_area": SAMPLE_RESUME,
        "target_role_choice": "Business Analyst",
        "custom_target_role": "",
        "target_location_choice": "San Francisco Bay Area",
        "custom_target_location": "",
        "coursework_selection": SAMPLE_COURSEWORK,
        "additional_coursework": "",
        "resume_draft": "",
        "selected_resume_template": "Use my existing resume structure",
        "custom_resume_template": "",
        "resume_job_post": "",
        "resume_profile_resume_editor": "",
        "resume_profile_source_snapshot": "",
        "tailored_resume_history": [],
        "practice_questions": None,
        "interview_evaluation": None,
        "presenter_mode": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_demo_profile() -> None:
    st.session_state.analysis = None
    st.session_state.latency_seconds = None
    st.session_state.active_view = "Dashboard"
    st.session_state.last_resume_upload = None
    st.session_state.resume_upload_notice = "Sample MIS graduate profile restored."
    st.session_state.resume_text_area = SAMPLE_RESUME
    st.session_state.target_role_choice = "Business Analyst"
    st.session_state.custom_target_role = ""
    st.session_state.target_location_choice = "San Francisco Bay Area"
    st.session_state.custom_target_location = ""
    st.session_state.coursework_selection = SAMPLE_COURSEWORK
    st.session_state.additional_coursework = ""
    st.session_state.resume_draft = ""
    st.session_state.selected_resume_template = "Use my existing resume structure"
    st.session_state.custom_resume_template = ""
    st.session_state.resume_job_post = ""
    st.session_state.resume_profile_resume_editor = SAMPLE_RESUME
    st.session_state.resume_profile_source_snapshot = SAMPLE_RESUME
    st.session_state.tailored_resume_history = []
    st.session_state.practice_questions = None
    st.session_state.interview_evaluation = None
    st.session_state.demo_autorun_view = None


def update_saved_resume_from_editor() -> None:
    edited_resume = st.session_state.get("resume_profile_resume_editor", "")
    st.session_state.resume_text_area = edited_resume
    st.session_state.resume_profile_source_snapshot = edited_resume.strip()


def clear_resume_job_post() -> None:
    st.session_state.resume_job_post = ""


def sample_demo_inputs() -> dict:
    return {
        "resume_text": SAMPLE_RESUME,
        "target_role": "Business Analyst",
        "target_location": "San Francisco Bay Area",
        "timeline_days": 90,
        "coursework": SAMPLE_COURSEWORK,
    }


def apply_demo_query_params() -> None:
    if st.query_params.get("demo_autorun") != "1":
        return

    view_param = st.query_params.get("demo_view", "dashboard")
    st.session_state.active_view = DEMO_VIEW_PARAMS.get(view_param, "Dashboard")

    if st.session_state.get("demo_autorun_view") == view_param and st.session_state.analysis:
        return

    started_at = time.perf_counter()
    st.session_state.analysis = run_career_analysis(sample_demo_inputs())
    st.session_state.latency_seconds = time.perf_counter() - started_at
    st.session_state.practice_questions = None
    st.session_state.interview_evaluation = None
    st.session_state.demo_autorun_view = view_param


def render_sidebar() -> None:
    st.sidebar.title("CareerCompass")
    st.sidebar.caption("Career strategy workspace")
    st.sidebar.divider()
    st.sidebar.write("Build a profile, compare role gaps, tailor resumes, and practice interviews.")


def render_role_status_panel() -> None:
    cards = []
    for item in ROLE_STATUS:
        cards.append(
            f"""
            <div class="cc-status">
                <strong>{item['owner']} - {item['lane']}</strong>
                <span>{item['status']}</span>
                <p>{item['summary']}</p>
            </div>
            """
        )
    st.markdown(
        f"""<div class="cc-status-grid">{''.join(cards)}</div>""",
        unsafe_allow_html=True,
    )


def render_presenter_cue(view_name: str) -> None:
    if not st.session_state.presenter_mode:
        return

    cue = DEMO_CUES.get(view_name)
    if not cue:
        return

    st.markdown(
        f"""
        <div class="cc-demo-cue">
            <strong>Presenter cue:</strong> {cue}
        </div>
        """,
        unsafe_allow_html=True,
    )


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

    reset_col, note_col = st.columns([0.35, 0.65])
    with reset_col:
        if st.button("Reset sample demo profile"):
            reset_demo_profile()
            st.rerun()
    with note_col:
        st.caption(
            "Use reset before recording so the walkthrough starts from a predictable sample profile."
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
        role_options = available_target_roles() + ["Custom role"]
        if st.session_state.target_role_choice not in role_options:
            st.session_state.target_role_choice = role_options[0]

        target_role_choice = st.selectbox(
            "Target role",
            options=role_options,
            key="target_role_choice",
            help="Choose a role from the current job-posting dataset, or use Custom role for another target.",
        )
        if target_role_choice == "Custom role":
            target_role = st.text_input(
                "Custom target role",
                key="custom_target_role",
                placeholder="Example: Product Analyst, Data Engineer, UX Researcher",
            ).strip()
        else:
            target_role = target_role_choice

        location_options = available_locations() + ["Custom location"]
        if st.session_state.target_location_choice not in location_options:
            st.session_state.target_location_choice = location_options[0]

        target_location_choice = st.selectbox(
            "Target location",
            options=location_options,
            key="target_location_choice",
            help="Locations come from the current local job-posting dataset.",
        )
        if target_location_choice == "Custom location":
            target_location = st.text_input(
                "Custom target location",
                key="custom_target_location",
                placeholder="Example: Los Angeles, Remote, New York",
            ).strip()
        else:
            target_location = target_location_choice

        timeline_days = st.slider(
            "Timeline (days until target hire date)",
            min_value=30,
            max_value=180,
            value=90,
            step=30,
        )
        coursework_options = available_coursework_options()
        selected_defaults = [
            option for option in st.session_state.coursework_selection if option in coursework_options
        ]
        if selected_defaults != st.session_state.coursework_selection:
            st.session_state.coursework_selection = selected_defaults

        coursework = st.multiselect(
            "Relevant coursework",
            options=coursework_options,
            key="coursework_selection",
            help="Options are expanded from the skills represented in the local job-posting dataset.",
        )
        additional_coursework = st.text_area(
            "Additional coursework or training",
            key="additional_coursework",
            height=92,
            placeholder="Add courses, certifications, bootcamps, or workshops separated by commas or new lines.",
        )
        coursework = merge_coursework(coursework, additional_coursework)

    return {
        "resume_text": resume_text,
        "target_role": target_role or "Business Analyst",
        "target_location": target_location or "San Francisco Bay Area",
        "timeline_days": timeline_days,
        "coursework": coursework,
    }


def merge_coursework(selected: list[str], additional_text: str) -> list[str]:
    additional = [
        chunk.strip()
        for chunk in additional_text.replace("\n", ",").split(",")
        if chunk.strip()
    ]
    merged = []
    for item in [*selected, *additional]:
        if item not in merged:
            merged.append(item)
    return merged


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
    retrieved_postings = analysis.get("retrieved_job_postings", [])
    if retrieved_postings:
        with st.expander("Retrieved job-posting evidence"):
            evidence_rows = [
                {
                    "Company": posting["company"],
                    "Role": posting["role"],
                    "Location": posting["location"],
                    "Score": posting["retrieval_score"],
                    "Evidence": posting["evidence_summary"],
                }
                for posting in retrieved_postings
            ]
            st.dataframe(pd.DataFrame(evidence_rows), use_container_width=True, hide_index=True)

    st.subheader("Skill gap report")
    gaps = pd.DataFrame(analysis["gap_report"])
    st.dataframe(gaps, use_container_width=True, hide_index=True)

    st.subheader("Suggested certifications and short courses")
    st.dataframe(
        pd.DataFrame(analysis["certification_recommendations"]),
        use_container_width=True,
        hide_index=True,
    )

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
    cols = st.columns(3)
    for col, phase in zip(cols, analysis["learning_roadmap"]):
        with col:
            st.subheader(phase["period"])
            st.write(phase["goal"])
            for task in phase["tasks"]:
                st.checkbox(task, value=False, key=f"{phase['period']}-{task}")
            st.caption(f"Resource relevance: {phase['resource_relevance']}/5")

    st.subheader("Portfolio proof ideas")
    for item in analysis["portfolio_ideas"]:
        st.checkbox(item, value=False, key=f"portfolio-{item}")


def render_resume(analysis: dict) -> None:
    st.header("Resume Optimization")
    st.caption("Reuse the saved profile resume, paste a job post, generate a targeted draft, then export.")

    st.subheader("Resume keyword targets")
    st.write(
        "These are the words and phrases CareerCompass thinks should be represented somewhere in the resume."
    )
    keyword_df = pd.DataFrame(analysis["keyword_targets"])
    st.dataframe(keyword_df, use_container_width=True, hide_index=True)

    st.subheader("Resume evidence reminders")
    st.caption("Use these while reviewing the tailored draft for this job post.")
    for item in analysis["resume_checklist"]:
        st.checkbox(item, value=False, key=f"resume-check-{item}")

    saved_resume = st.session_state.resume_text_area.strip()
    if st.session_state.resume_profile_source_snapshot != saved_resume:
        st.session_state.resume_profile_resume_editor = saved_resume
        st.session_state.resume_profile_source_snapshot = saved_resume

    st.subheader("Tailor your resume to a specific job")
    st.caption(
        "Paste the job description here. We'll use your saved resume and the job requirements to rebuild a targeted version of your resume."
    )
    with st.expander("Review or replace the saved profile resume"):
        st.write("This is the resume from the Build your career profile step. Edit it here only if you want to replace the saved version for this application batch.")
        edited_saved_resume = st.text_area(
            "Saved profile resume",
            height=260,
            key="resume_profile_resume_editor",
        )
        if st.button("Update saved profile resume from this editor", on_click=update_saved_resume_from_editor):
            st.success("Saved profile resume updated for future tailored drafts.")

    job_post = st.text_area(
        "Paste the job post you're applying to",
        key="resume_job_post",
        height=240,
        placeholder="Paste the full job description, responsibilities, qualifications, and preferred skills here.",
    )
    job_keywords = derive_job_post_keywords(job_post, analysis)
    if job_keywords:
        st.markdown("**Job-specific keyword signals**")
        st.dataframe(pd.DataFrame(job_keywords), use_container_width=True, hide_index=True)
    else:
        st.info("Paste a job post to add job-specific keywords to the existing CareerCompass resume targets.")

    evidence_map = build_skill_evidence_map(
        analysis=analysis,
        resume_text=st.session_state.resume_text_area,
        coursework=merge_coursework(
            st.session_state.coursework_selection,
            st.session_state.additional_coursework,
        ),
        job_post=job_post,
    )
    st.subheader("Skill Evidence Map")
    st.caption("Use this to see what CareerCompass found before generating the tailored resume.")
    st.dataframe(pd.DataFrame(evidence_map), use_container_width=True, hide_index=True)

    st.subheader("Choose a resume format")
    st.write("The selected format will restructure your saved resume for the pasted job post, not just apply a generic template.")
    format_options = [
        "Use my existing resume structure",
        "Project-forward resume",
        "Experience-forward resume",
        "Skills matrix resume",
        "Custom student-supplied template",
    ]
    if st.session_state.selected_resume_template not in format_options:
        st.session_state.selected_resume_template = "Use my existing resume structure"
    format_name = st.selectbox(
        "Resume format",
        options=format_options,
        key="selected_resume_template",
        help="Choose how the tailored resume should be organized for this job post.",
    )
    template_name = resume_format_template_key(format_name)

    custom_template = ""
    if format_name == "Custom student-supplied template":
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
        template = resume_format_metadata(format_name, analysis, template_name)

    t1, t2 = st.columns([0.9, 1.1])
    with t1:
        st.markdown(f"**Best for:** {template['best_for']}")
        st.markdown("**Recommended sections**")
        for section in template["sections"] or ["Custom section order will appear here."]:
            st.write(f"- {section}")
    with t2:
        preview = build_resume_draft(analysis, template_name, custom_template)
        st.text_area("Structure preview", value=preview, height=280)
        if st.button("Save structure preview to editable resume"):
            st.session_state.resume_draft = preview
            st.success("Structure preview copied into the editable resume draft.")

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

    st.subheader("Generate job-specific resume")
    generate_col, clear_col = st.columns([1, 1])
    with generate_col:
        if st.button("Generate tailored resume", type="primary"):
            if not st.session_state.resume_job_post.strip():
                st.warning("Paste a job post first so CareerCompass can tailor the resume to that application.")
            else:
                tailored = build_tailored_resume_draft(
                    analysis=analysis,
                    saved_resume=st.session_state.resume_text_area,
                    job_post=st.session_state.resume_job_post,
                    format_name=format_name,
                    custom_template=custom_template,
                    selected_suggestions=selected_suggestions,
                )
                st.session_state.resume_draft = tailored
                st.session_state.tailored_resume_history = [
                    {
                        "Job": infer_job_title(st.session_state.resume_job_post, analysis),
                        "Format": format_name,
                        "Keyword count": len(derive_job_post_keywords(st.session_state.resume_job_post, analysis)),
                    },
                    *st.session_state.tailored_resume_history[:4],
                ]
                st.success("Tailored resume generated. Paste another job post and run again for the next application.")
    with clear_col:
        if st.button("Clear job post for next application", on_click=clear_resume_job_post):
            st.success("Job post cleared. Your saved profile resume is still available.")

    if st.session_state.tailored_resume_history:
        st.caption("Recent tailored resume runs")
        st.dataframe(pd.DataFrame(st.session_state.tailored_resume_history), use_container_width=True, hide_index=True)

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
    question_options = list(range(len(questions)))
    selected_index = st.radio(
        "Choose a question to practice",
        options=question_options,
        format_func=lambda index: _question_picker_label(questions[index]),
    )

    selected_detail = questions[selected_index]
    selected_question = selected_detail["question"]
    st.markdown("**Practice question**")
    st.write(selected_question)
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


def _question_picker_label(question: dict) -> str:
    text = " ".join(str(question.get("question", "")).split())
    if len(text) > 92:
        text = text[:89].rsplit(" ", 1)[0].rstrip(",.;:") + "..."
    return f"{question.get('type', 'Question')}: {text}"


def render_report(analysis: dict) -> None:
    st.header("Final Strategy Report")
    st.text_area("Copyable report", value=analysis["final_strategy_report"], height=360)

    st.warning(
        "CareerCompass recommendations are decision support, not a guarantee. Students should review outputs with a career advisor."
    )


def render_action_checklist(analysis: dict) -> None:
    st.header("Action Checklist")
    st.caption("Use this as a reminder system for missing resume evidence, certifications, and portfolio proof.")

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
    render_sidebar()
    apply_demo_query_params()

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

    if st.session_state.analysis:
        views = [
            "Dashboard",
            "Roadmap",
            "Resume",
            "Interview",
            "Final Report",
        ]
        active_view = st.radio(
            "CareerCompass workspace",
            options=views,
            horizontal=True,
            key="active_view",
        )
        if active_view == "Dashboard":
            render_dashboard(st.session_state.analysis)
        elif active_view == "Roadmap":
            render_roadmap(st.session_state.analysis)
        elif active_view == "Resume":
            render_resume(st.session_state.analysis)
        elif active_view == "Interview":
            render_interview(st.session_state.analysis)
        elif active_view == "Final Report":
            render_report(st.session_state.analysis)


JOB_KEYWORD_ALIASES = {
    "SQL": ["sql", "query", "queries", "database"],
    "Python": ["python", "pandas", "notebook"],
    "Excel": ["excel", "spreadsheet", "pivot"],
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi"],
    "Dashboarding": ["dashboard", "dashboards", "reporting", "visualization"],
    "Data analysis": ["data analysis", "analytics", "insights", "trend"],
    "A/B testing": ["a/b", "experiment", "experimentation", "conversion"],
    "Requirements gathering": ["requirements", "user stories", "acceptance criteria"],
    "Stakeholder communication": ["stakeholder", "cross-functional", "presentation", "executive"],
    "Project management": ["project management", "timeline", "milestone", "delivery"],
    "Agile / Scrum": ["agile", "scrum", "sprint", "backlog"],
    "Risk management": ["risk", "mitigation", "blocker", "dependency"],
    "Customer insight": ["customer", "user research", "persona", "voice of customer"],
    "Product marketing": ["product marketing", "launch", "campaign", "positioning"],
    "Process improvement": ["process improvement", "workflow", "automation", "operational"],
}


RESUME_SECTION_ALIASES = {
    "SUMMARY": "SUMMARY",
    "PROFILE": "SUMMARY",
    "PROFESSIONAL SUMMARY": "SUMMARY",
    "OBJECTIVE": "SUMMARY",
    "SKILLS": "SKILLS",
    "TECHNICAL SKILLS": "SKILLS",
    "CORE COMPETENCIES": "SKILLS",
    "EDUCATION": "EDUCATION",
    "ACADEMIC BACKGROUND": "EDUCATION",
    "EXPERIENCE": "EXPERIENCE",
    "WORK EXPERIENCE": "EXPERIENCE",
    "PROFESSIONAL EXPERIENCE": "EXPERIENCE",
    "EMPLOYMENT": "EXPERIENCE",
    "MILITARY EXPERIENCE": "EXPERIENCE",
    "LEADERSHIP EXPERIENCE": "EXPERIENCE",
    "PROJECTS": "PROJECTS",
    "PROJECT EXPERIENCE": "PROJECTS",
    "SELECTED PROJECTS": "PROJECTS",
    "CERTIFICATIONS": "CERTIFICATIONS",
    "CERTIFICATION": "CERTIFICATIONS",
    "CLEARANCE": "CERTIFICATIONS",
    "AWARDS": "ADDITIONAL",
    "VOLUNTEER": "ADDITIONAL",
    "LANGUAGES": "ADDITIONAL",
}


def resume_format_template_key(format_name: str) -> str:
    mapping = {
        "Use my existing resume structure": "ATS chronological",
        "Project-forward resume": "Project-forward",
        "Experience-forward resume": "ATS chronological",
        "Skills matrix resume": "Skills matrix",
        "Custom student-supplied template": "Use my own template",
    }
    return mapping.get(format_name, "ATS chronological")


def resume_format_metadata(format_name: str, analysis: dict, template_name: str) -> dict:
    if format_name == "Use my existing resume structure":
        return {
            "best_for": "Keeping the saved resume familiar while retargeting summary, skills, and bullets to the pasted job post.",
            "sections": ["Header", "Summary", "Education", "Experience or Projects", "Skills", "Certifications"],
        }
    if format_name == "Experience-forward resume":
        return {
            "best_for": "Applications where the posting emphasizes ownership, impact, collaboration, or repeated work experience.",
            "sections": ["Header", "Targeted Summary", "Core Skills", "Experience", "Projects", "Education"],
        }
    if template_name in analysis["resume_templates"]:
        return analysis["resume_templates"][template_name]
    return {
        "best_for": "A targeted resume structure for the pasted job post.",
        "sections": ["Header", "Summary", "Skills", "Projects", "Education"],
    }


def derive_job_post_keywords(job_post: str, analysis: dict, limit: int = 12) -> list[dict]:
    text = normalize_text(job_post)
    if not text:
        return []

    rows = []
    existing_keywords = [item["Keyword"] for item in analysis.get("keyword_targets", [])]
    candidate_labels = [*existing_keywords, *JOB_KEYWORD_ALIASES.keys()]
    seen = set()

    for label in candidate_labels:
        normalized_label = label.lower()
        if normalized_label in seen:
            continue
        aliases = JOB_KEYWORD_ALIASES.get(label, [label])
        if any(alias.lower() in text for alias in aliases):
            rows.append(
                {
                    "Keyword": label,
                    "Source": "Job post",
                    "How to use it": job_keyword_usage(label),
                }
            )
            seen.add(normalized_label)

    for phrase in extract_repeated_job_phrases(job_post):
        normalized_phrase = phrase.lower()
        if normalized_phrase not in seen:
            rows.append(
                {
                    "Keyword": phrase,
                    "Source": "Repeated phrase",
                    "How to use it": "Mirror this phrase only where your saved resume has matching evidence.",
                }
            )
            seen.add(normalized_phrase)
        if len(rows) >= limit:
            break

    return rows[:limit]


def build_skill_evidence_map(
    analysis: dict,
    resume_text: str,
    coursework: list[str],
    job_post: str = "",
) -> list[dict]:
    job_keywords = derive_job_post_keywords(job_post, analysis)
    job_keyword_names = [item["Keyword"] for item in job_keywords]
    market_skill_demand = {
        item["Skill"]: item.get("Demand Signal", "Medium")
        for item in analysis.get("market_skills", [])
    }
    candidate_skills = merge_unique(
        job_keyword_names,
        [
            *[item["Keyword"] for item in analysis.get("keyword_targets", [])],
            *market_skill_demand.keys(),
        ],
    )[:14]

    rows = []
    for skill in candidate_skills:
        evidence = assess_skill_evidence(skill, resume_text, coursework)
        demand = "Job post" if skill in job_keyword_names else market_skill_demand.get(skill, "Profile target")
        rows.append(
            {
                "Skill": skill,
                "Job Demand": demand,
                "Resume Evidence": evidence["status"],
                "Found In": evidence["evidence_source"],
                "Evidence Excerpt": evidence["evidence_excerpt"],
                "Gap Action": skill_gap_action(skill, evidence["status"], demand),
            }
        )
    return rows


def skill_gap_action(skill: str, status: str, demand: str) -> str:
    if status == "Strong Evidence":
        return "Keep it visible and quantify the outcome if possible."
    if status == "Mentioned":
        return f"Add a bullet showing how you used {skill} in a project, job, or coursework deliverable."
    if demand == "Job post":
        return f"Add truthful {skill} evidence or avoid over-claiming it for this application."
    return f"Build or document one small proof point for {skill}."


def job_keyword_usage(keyword: str) -> str:
    lower_keyword = keyword.lower()
    if any(term in lower_keyword for term in ["sql", "python", "excel", "tableau", "power bi", "dashboard"]):
        return "Name the tool near a project, analysis task, or measurable deliverable."
    if any(term in lower_keyword for term in ["stakeholder", "requirements", "project", "agile", "risk"]):
        return "Use it in an impact bullet that shows coordination, decisions, or delivery."
    if any(term in lower_keyword for term in ["marketing", "customer", "testing", "process"]):
        return "Connect it to customer insight, experiments, workflow improvement, or launch outcomes."
    return "Place it in the summary, skills, or a bullet only when supported by your resume evidence."


def extract_repeated_job_phrases(job_post: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z+#/.-]{2,}", job_post.lower())
    stop_words = {
        "and",
        "the",
        "for",
        "with",
        "you",
        "our",
        "will",
        "this",
        "that",
        "from",
        "are",
        "have",
        "your",
        "work",
        "team",
        "role",
        "skills",
        "experience",
        "ability",
    }
    counts = {}
    for word in words:
        if word in stop_words or len(word) < 4:
            continue
        counts[word] = counts.get(word, 0) + 1

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [word.title() if word in {"sql", "python", "tableau"} else word for word, count in ranked if count >= 2][:5]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def infer_job_title(job_post: str, analysis: dict) -> str:
    lines = [line.strip(" -|") for line in job_post.splitlines() if line.strip()]
    for line in lines[:6]:
        if 3 <= len(line) <= 80 and not line.endswith("."):
            return line
    return analysis.get("target_role") or analysis.get("role_label") or "Target job"


def parse_resume_sections(saved_resume: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"HEADER": []}
    current = "HEADER"

    for raw_line in saved_resume.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading, remainder = split_resume_heading(line)
        if heading:
            current = heading
            sections.setdefault(current, [])
            if remainder:
                sections[current].append(remainder)
            continue

        sections.setdefault(current, []).append(line)

    return sections


def split_resume_heading(line: str) -> tuple[str | None, str]:
    normalized = re.sub(r"[^A-Za-z ]", "", line).strip().upper()
    if normalized in RESUME_SECTION_ALIASES:
        return RESUME_SECTION_ALIASES[normalized], ""

    if ":" in line:
        prefix, remainder = line.split(":", 1)
        normalized_prefix = re.sub(r"[^A-Za-z ]", "", prefix).strip().upper()
        if normalized_prefix in RESUME_SECTION_ALIASES:
            return RESUME_SECTION_ALIASES[normalized_prefix], remainder.strip()

    return None, ""


def extract_resume_identity(saved_resume: str) -> dict[str, str]:
    sections = parse_resume_sections(saved_resume)
    header_lines = sections.get("HEADER", [])
    fallback_lines = [line.strip() for line in saved_resume.splitlines() if line.strip()]
    candidate_lines = header_lines or fallback_lines[:6]

    email = find_first(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", saved_resume)
    phone = find_first(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", saved_resume)
    links = re.findall(r"(?:https?://)?(?:www\.)?(?:linkedin\.com|github\.com|[\w.-]+\.(?:com|net|io|me))/\S+", saved_resume, flags=re.IGNORECASE)

    name = "NAME"
    for line in candidate_lines:
        if line == email or line == phone:
            continue
        if email and email.lower() in line.lower():
            continue
        if phone and phone in line:
            continue
        if not has_contact_signal(line) and len(line.split()) <= 5:
            name = line.strip(" -")
            break

    location = ""
    for line in candidate_lines:
        if line == name or has_contact_signal(line):
            continue
        if any(char.isdigit() for char in line) and "," in line:
            location = line
            break

    contact_parts = [part for part in [email, phone, *links[:2], location] if part]
    return {
        "name": name,
        "contact": " | ".join(dict.fromkeys(contact_parts)),
    }


def find_first(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(0) if match else ""


def has_contact_signal(line: str) -> bool:
    lower_line = line.lower()
    return bool(
        "@" in line
        or re.search(r"\d{3}[-.\s)]?\d{3}[-.\s]?\d{4}", line)
        or "linkedin" in lower_line
        or "github" in lower_line
        or "portfolio" in lower_line
        or "http" in lower_line
    )


def extract_resume_education(saved_resume: str) -> list[str]:
    sections = parse_resume_sections(saved_resume)
    education = clean_resume_lines(sections.get("EDUCATION", []))
    if education:
        return education

    degree_signals = ["degree", "bachelor", "master", "associate", "college", "university", "school", "sfsu"]
    return [
        line.strip()
        for line in saved_resume.splitlines()
        if any(signal in line.lower() for signal in degree_signals)
    ][:8]


def extract_resume_skills(saved_resume: str) -> list[str]:
    sections = parse_resume_sections(saved_resume)
    skills = clean_resume_lines(sections.get("SKILLS", []))
    return split_inline_items(skills)[:16]


def extract_resume_bullets(saved_resume: str, limit: int = 6) -> list[str]:
    sections = parse_resume_sections(saved_resume)
    source_lines = []
    for section in ["EXPERIENCE", "PROJECTS", "SUMMARY", "ADDITIONAL"]:
        source_lines.extend(sections.get(section, []))

    bullets = []
    for line in clean_resume_lines(source_lines):
        if has_contact_signal(line):
            continue
        if looks_like_education_line(line):
            continue
        if split_resume_heading(line)[0]:
            continue
        bullets.extend(split_resume_line_into_bullets(line))

    return bullets[:limit]


def clean_resume_lines(lines: list[str]) -> list[str]:
    cleaned = []
    for line in lines:
        stripped = line.strip().lstrip("-*• ").strip()
        if stripped and stripped not in cleaned:
            cleaned.append(stripped)
    return cleaned


def split_inline_items(lines: list[str]) -> list[str]:
    items = []
    for line in lines:
        chunks = re.split(r",|;|\|", line)
        for chunk in chunks:
            item = chunk.strip()
            if item and item not in items:
                items.append(item)
    return items or lines


def split_resume_line_into_bullets(line: str) -> list[str]:
    stripped = line.strip().lstrip("-*• ").strip()
    if len(stripped) > 220:
        parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", stripped) if len(part.strip()) > 35]
        return parts or [stripped[:217].rstrip(",.;:") + "..."]
    return [stripped]


def looks_like_education_line(line: str) -> bool:
    lower_line = line.lower()
    return any(
        signal in lower_line
        for signal in ["bachelor", "master", "associate", "college", "university", "degree", "sfsu", "gpa"]
    )


def keyword_names(analysis: dict, job_post: str) -> list[str]:
    names = [item["Keyword"] for item in derive_job_post_keywords(job_post, analysis)]
    for item in analysis.get("keyword_targets", []):
        if item["Keyword"] not in names:
            names.append(item["Keyword"])
    return names[:10]


def build_tailored_resume_draft(
    analysis: dict,
    saved_resume: str,
    job_post: str,
    format_name: str,
    custom_template: str = "",
    selected_suggestions: list[dict] | None = None,
) -> str:
    role = analysis.get("role_label", analysis.get("target_role", "Target Role"))
    job_title = infer_job_title(job_post, analysis)
    keywords = keyword_names(analysis, job_post)
    keyword_line = ", ".join(keywords[:8])
    identity = extract_resume_identity(saved_resume)
    education_lines = extract_resume_education(saved_resume)
    saved_skills = extract_resume_skills(saved_resume)
    source_bullets = extract_resume_bullets(saved_resume)
    suggestion_bullets = [item["after"] for item in selected_suggestions or []]
    if not suggestion_bullets:
        suggestion_bullets = [item["after"] for item in analysis.get("resume_recommendations", [])[:3]]

    targeted_bullets = tailor_bullets(source_bullets, suggestion_bullets, keywords)
    skills = ", ".join(keywords[:10])
    candidate_label = f"{role} candidate" if role.lower() in job_title.lower() else "candidate"
    summary = (
        f"Early-career {candidate_label} targeting {job_title} with evidence across "
        f"{keyword_line}. Brings coursework, project delivery, and stakeholder-focused problem solving."
    )
    header = identity["name"]
    if identity["contact"]:
        header += f"\n{identity['contact']}"
    education = "\n".join(education_lines) if education_lines else "Add education from saved resume."
    skills_with_resume = merge_unique(saved_skills, keywords)[:14]
    skills = ", ".join(skills_with_resume)
    improvements = "\n".join(f"- {bullet}" for bullet in suggestion_bullets[:4])

    section_map = {
        "HEADER": header,
        "SUMMARY": f"SUMMARY\n{summary}",
        "TARGETED SKILLS": f"TARGETED SKILLS\n{skills}",
        "EXPERIENCE": "EXPERIENCE\n" + "\n".join(f"- {bullet}" for bullet in targeted_bullets),
        "PROJECT EXPERIENCE": "PROJECT EXPERIENCE\n" + "\n".join(f"- {bullet}" for bullet in targeted_bullets),
        "EDUCATION": f"EDUCATION\n{education}",
        "SOURCE RESUME EVIDENCE": "SOURCE RESUME EVIDENCE\n" + "\n".join(f"- {bullet}" for bullet in source_bullets[:4]),
        "CAREERCOMPASS IMPROVEMENTS": f"CAREERCOMPASS IMPROVEMENTS\n{improvements}",
        "JOB POST TARGETS": "JOB POST TARGETS\n" + "\n".join(f"- {keyword}" for keyword in keywords[:8]),
    }

    if format_name == "Custom student-supplied template" and custom_template.strip():
        custom_sections = [line.strip().upper() for line in custom_template.splitlines() if line.strip()]
        rendered = [section_map["HEADER"]]
        for section in custom_sections:
            rendered.append(section_map.get(section, f"{section}\nAdd content here using saved resume evidence and job-post keywords."))
        rendered.append(section_map["CAREERCOMPASS IMPROVEMENTS"])
        rendered.append(section_map["JOB POST TARGETS"])
        return "\n\n".join(rendered).strip() + "\n"

    if format_name == "Project-forward resume":
        order = ["HEADER", "SUMMARY", "TARGETED SKILLS", "PROJECT EXPERIENCE", "EDUCATION", "CAREERCOMPASS IMPROVEMENTS", "JOB POST TARGETS"]
    elif format_name == "Experience-forward resume":
        order = ["HEADER", "SUMMARY", "TARGETED SKILLS", "EXPERIENCE", "EDUCATION", "CAREERCOMPASS IMPROVEMENTS"]
    elif format_name == "Skills matrix resume":
        order = ["HEADER", "SUMMARY", "TARGETED SKILLS", "SOURCE RESUME EVIDENCE", "PROJECT EXPERIENCE", "EDUCATION", "CAREERCOMPASS IMPROVEMENTS"]
    else:
        order = ["HEADER", "SUMMARY", "EXPERIENCE", "EDUCATION", "TARGETED SKILLS", "CAREERCOMPASS IMPROVEMENTS", "JOB POST TARGETS"]

    return "\n\n".join(section_map[section] for section in order).strip() + "\n"


def tailor_bullets(source_bullets: list[str], suggestion_bullets: list[str], keywords: list[str]) -> list[str]:
    combined = [*source_bullets[:4], *suggestion_bullets[:3]]
    if not combined:
        combined = ["Completed coursework and projects aligned to the target role."]

    tailored = []
    for index, bullet in enumerate(combined[:6]):
        keyword = keywords[index % len(keywords)] if keywords else "target role requirements"
        if keyword.lower() in bullet.lower():
            tailored.append(bullet)
        else:
            tailored.append(f"{bullet} Emphasized {keyword} based on the target job requirements.")
    return tailored


def merge_unique(primary: list[str], secondary: list[str]) -> list[str]:
    merged = []
    for item in [*primary, *secondary]:
        cleaned = item.strip()
        if cleaned and cleaned.lower() not in {existing.lower() for existing in merged}:
            merged.append(cleaned)
    return merged


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
