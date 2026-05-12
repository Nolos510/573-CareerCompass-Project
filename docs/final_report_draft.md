# CareerCompass Final Report Draft

An Agentic AI System for Personalized Career Strategy and Skill Development

Draft purpose: this document is an independent report draft for the final submission teammate to compare against the official report. It is intentionally written as a complete narrative rather than a short outline. The team may merge stronger wording, tables, and evidence references into the final formatted submission.

## 1. Executive Summary And Problem Statement

CareerCompass is an agentic AI career strategy MVP designed to help students and recent graduates turn scattered career inputs into a structured, evidence-grounded plan. The system takes resume text, relevant coursework, a target role, a target location, and a timeline, then coordinates multiple specialized agents to produce a personalized career strategy. The current demo scenario focuses on a recent Management Information Systems graduate targeting Business Analyst or Project Manager style roles in the San Francisco Bay Area within a 90-day timeline.

The core problem is that early-career job seekers often have partial evidence of their skills but struggle to translate that evidence into a coherent job-search plan. A student may have coursework in databases, business analytics, and project management, but still lack visible portfolio proof, role-specific resume language, and interview practice. Career advice is also often generic. Students are told to "improve the resume," "learn Tableau," or "network more," but those recommendations are rarely tied to a specific role, local market evidence, or a realistic timeline.

CareerCompass addresses this gap by acting as a career strategy workspace rather than a generic chatbot. It uses a supervisor workflow to route the student's profile through specialist agents for labor-market evidence, skill gap analysis, curriculum planning, resume optimization, interview simulation, and final synthesis. The goal is not to guarantee job placement or replace a human advisor. Instead, the system provides decision support: it helps the student see which skill gaps matter, what evidence to create, how to revise resume bullets without inventing claims, and how to practice for interviews using role-relevant prompts.

The MVP was built as a Streamlit application with deterministic fallback behavior so it can be demonstrated reliably without API keys, network access, or live job-board integrations. Optional OpenAI-backed structured model calls are scaffolded through the agent-logic layer, but the demo-safe default uses deterministic, testable behavior. This design supports the class requirement to demonstrate an agentic AI system while also preserving predictable outputs for a final video and presentation.

CareerCompass maps to Track B, Agentic AI System, because it is not a single prompt or one-shot model call. The architecture includes a supervisor, multiple specialist agents, shared typed state, inter-agent handoff records, retrieved job-posting evidence, final synthesis, evaluation metrics, and visible responsible-AI controls. The project also includes a Docker deployment path, local evaluation results, ethics documentation, screenshots, and a demo flow for the final video.

## 2. Business Value And Target Users

The primary target user is a student or recent graduate preparing for an early-career role. The initial persona is a recent MIS graduate targeting Business Analyst or Project Manager roles in the Bay Area. This user has relevant coursework and some technical/business exposure, but may not know how to present those experiences in a way that aligns with employer expectations.

The secondary target user is a career center or academic program that supports many students with similar needs. Career advisors often have limited time per student. A tool like CareerCompass can help students arrive at advising sessions with a clearer view of their target role, gaps, resume evidence, and next actions. This makes human advising more efficient without removing the advisor from the loop.

CareerCompass creates business value in four main ways.

First, it converts vague career preparation into concrete next actions. Instead of saying "improve analytics skills," the system identifies specific gaps such as Power BI, Tableau, KPIs, Agile, Jira, risk management, or requirements gathering depending on the target role and retrieved job evidence. It then connects those gaps to first steps, portfolio proof, and resume language.

Second, it grounds recommendations in market evidence. The Market Demand Agent retrieves local job postings and derives recurring skills from those postings. The user can see retrieved evidence rather than receiving unsupported advice. The current local corpus is intentionally small and directional, but it demonstrates the architecture for evidence-grounded recommendations.

Third, it improves the job-search workflow across multiple surfaces. The app does not stop at a dashboard. It includes a roadmap, resume suggestions, an editable resume draft, interview questions, answer evaluation, action checklist, final report, and rubric evidence. This helps the student move from analysis to execution.

Fourth, it supports responsible use. The system reminds users that recommendations are decision support, not guarantees. It includes advisor-review language, confidence scores, visible retrieved evidence, privacy notes, and warnings against exaggerating resume claims. This is important because career tools can influence real student decisions.

The practical value proposition is: CareerCompass helps students leave with a 30/60/90-day role-readiness plan backed by retrieved evidence, resume proof targets, and interview practice. For a class MVP, that is a clear, demo-ready business case with a plausible path toward a production advising tool.

## 3. Agent Architecture And Workflow

CareerCompass is organized as a multi-agent workflow coordinated by a supervisor. The Streamlit UI gathers the student's inputs and calls `run_career_analysis()`, which invokes the workflow in `careercompass/agents.py`. The workflow produces a validated `CareerStrategyOutput` contract with version `careercompass.strategy.v1`.

The main workflow is:

```text
Streamlit UI
  -> run_career_analysis()
  -> Supervisor Agent
  -> Market Demand Agent
  -> Gap Analysis Agent
  -> Curriculum Agent
  -> Resume Optimization Agent
  -> Interview Simulation Agent
  -> Synthesis Node
  -> CareerStrategyOutput
```

If `langgraph` is installed, `build_supervisor_workflow()` compiles a LangGraph `StateGraph`. If LangGraph is not available, `DeterministicCareerWorkflow` follows the same route and output contract. This fallback is important for demo reliability: the project can still run in environments that do not have the full graph dependency installed.

The shared state contract is defined in `careercompass/state.py`. The key structures include:

- `AgentState`: the shared state passed between workflow nodes.
- `AgentHandoff`: a traceable record of inter-agent coordination.
- `CareerStrategyOutput`: the Streamlit-facing output contract.
- `AgentName`: allowed workflow node names.
- `WorkflowIntent`: route intents such as full strategy, resume-only, or interview-only.

The supervisor starts by validating inputs and routing the request. The current demo path runs the full strategy workflow. The Market Demand Agent retrieves job-posting evidence and extracts relevant market skills. The Gap Analysis Agent compares the student's resume and coursework evidence against market signals. The Curriculum Agent converts gaps into a timeline-based roadmap. The Resume Optimization Agent suggests keyword targets, resume formats, and improved bullets. The Interview Simulation Agent creates practice questions and supports answer evaluation. The Synthesis Node combines the specialist outputs into the final student-facing strategy report.

The output is validated before it reaches the UI. `validate_final_output()` checks that required fields are present, the output contract version is supported, the agent trace starts with `supervisor` and ends with `synthesis`, and no queued handoffs remain after synthesis. This validation is a key part of making the app more than a visual prototype. It gives the team a contract that frontend, agent-logic, RAG, and evaluation lanes can preserve independently.

The dashboard exposes technical evidence for the class report, including agent coordination rows, raw inter-agent handoffs, confidence scores, and evaluation metrics. This makes the agentic workflow visible instead of hidden in backend code.

## 4. RAG And Data Design

CareerCompass currently uses a deterministic local retrieval layer over `careercompass/data/job_postings.json`. The dataset is intentionally lightweight so the MVP can run without scraping, API keys, live job-board access, or ChromaDB setup. It includes Bay Area and remote postings for roles such as Business Analyst, Data Analyst, Business Systems Analyst, Project Manager, Associate Project Manager, and Technical Project Coordinator.

The retrieval implementation lives in `careercompass/rag.py`. It follows a simple, demo-safe process:

1. Tokenize the target role and target location.
2. Score job postings by role, location, and skill overlap.
3. Return top postings with retrieval scores and evidence summaries.
4. Derive market skills by counting recurring skills across retrieved postings.

The retrieved posting shape is stable and should be preserved when the team upgrades to vector search:

```python
{
    "id": "...",
    "role": "...",
    "company": "...",
    "location": "...",
    "date": "...",
    "skills": ["..."],
    "description": "...",
    "retrieval_score": 1.0,
    "evidence_summary": "..."
}
```

This design gives the MVP a realistic RAG story without making the demo dependent on fragile external services. For the final submission, the current RAG layer should be described as a reliable local retrieval baseline. The production upgrade path is to ingest a larger Kaggle or LinkedIn-style job-posting dataset, embed postings with a model such as OpenAI `text-embedding-3-small`, store vectors in ChromaDB, and apply metadata filters for role, location, company, and posting date.

The limitation is important: the current local corpus is not representative of the full labor market. It is useful for a class demo and for showing how retrieved evidence flows into downstream agents, but it should not be presented as a statistically valid labor-market study. Bay Area tech postings are overrepresented, entry-level requirements vary by company, and skill counts from a small sample should be treated as directional. The final report should be explicit that retrieved evidence supports demo grounding, not authoritative market forecasting.

## 5. Implementation Details

The MVP is implemented as a Python Streamlit application. The primary entry point is `app.py`, which handles user inputs, state management, rendering, demo query parameters, resume upload extraction, workspace views, and export actions.

The core package is organized under `careercompass/`:

- `careercompass/agents.py`: supervisor workflow, specialist nodes, synthesis, output assembly.
- `careercompass/state.py`: shared workflow state and output contracts.
- `careercompass/rag.py`: local job-posting retrieval and market skill derivation.
- `careercompass/data/job_postings.json`: local demo job-posting corpus.
- `careercompass/agent_logic.py`: model-call hook plus validation and fallback selection.
- `careercompass/prompts.py`: prompt templates and JSON output instructions.
- `careercompass/schemas.py`: strict structured output schemas.
- `careercompass/fallbacks.py`: deterministic agent outputs for local demos and failures.
- `careercompass/llm_client.py`: optional OpenAI Responses API wrapper.
- `careercompass/demo_data.py`: default demo profile data.

The UI supports the full demo flow:

1. Career profile input, including resume paste/upload, role, location, timeline, and coursework.
2. Dashboard with readiness metrics, market demand summary, skill gap report, and gap deep dive.
3. 30/60/90-day roadmap.
4. Resume optimization with keyword targets, templates, selectable suggestions, editable draft, and TXT/DOCX export.
5. Interview simulation with scenario presets, company-specific questions, answer evaluation, score, feedback, and sample answer.
6. Final report with copyable strategy and advisor-review warning.
7. Action checklist for resume evidence, certifications, and portfolio proof.
8. Rubric Evidence view that maps features to Track B requirements.

The app defaults to deterministic fallback mode. Optional live LLM mode can be enabled with environment variables, but the class demo does not require it. The agent-logic documentation identifies both current and legacy environment variable names. The latest agent logic notes identify:

```powershell
$env:CAREERCOMPASS_LLM_ENABLED="true"
$env:OPENAI_API_KEY="<secret>"
$env:CAREERCOMPASS_OPENAI_MODEL="gpt-5.4-mini"
```

Deployment docs also mention legacy variables:

```powershell
$env:CAREERCOMPASS_USE_LLM="true"
$env:CAREERCOMPASS_LLM_MODEL="gpt-4o-mini"
```

Before final packaging, the team should ensure README and deployment docs consistently describe the preferred current variable names while noting legacy compatibility only if needed. No API keys should be hardcoded in source, docs, tests, or pull request comments.

The local run command is:

```powershell
C:\Users\knolo\anaconda3\python.exe -m streamlit run app.py --server.port 8503
```

The Docker path is:

```powershell
docker build -t careercompass .
docker run --rm -p 8501:8501 careercompass
```

Docker verification was completed in a prior handoff after Docker Desktop and WSL features were enabled. The image built successfully, the container served Streamlit at `http://localhost:8501`, and the temporary verification container was stopped afterward.

## 6. Evaluation Results

CareerCompass has evaluation evidence, but it should be framed accurately. The evaluation is a local smoke review and manual consistency check, not a statistically representative labor-market study. The purpose is to show that the MVP completes the end-to-end workflow, produces plausible role-specific outputs, retrieves evidence, and meets demo performance targets.

The local latency smoke test was measured on May 11, 2026 using Anaconda Python in deterministic fallback mode. The profile was an MIS graduate targeting Business Analyst roles in the San Francisco Bay Area. Five runs produced the following results:

| Run | Latency seconds | Match | Keyword coverage | Retrieved postings |
| --- | ---: | ---: | ---: | ---: |
| 1 | 2.1936 | 38% | 50% | 5 |
| 2 | 0.0148 | 38% | 50% | 5 |
| 3 | 0.0137 | 38% | 50% | 5 |
| 4 | 0.0148 | 38% | 50% | 5 |
| 5 | 0.0141 | 38% | 50% | 5 |

The average latency was 0.4502 seconds and the maximum observed latency was 2.1936 seconds. This passes the under-30-second demo target.

The three-profile smoke evaluation included:

| Profile | Match | Keyword coverage | Retrieved postings | Gap distribution | Roadmap relevance average | Interview questions |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| MIS to Business Analyst | 38% | 50% | 5 | 4 high, 0 medium, 4 low | 4.3/5 | 3 |
| MIS to Project Manager | 61% | 62% | 5 | 1 high, 2 medium, 5 low | 4.3/5 | 3 |
| Hybrid BA / PM | 46% | 50% | 5 | 2 high, 2 medium, 4 low | 4.3/5 | 3 |

Manual review compared high and medium gaps against retrieved market skills and resume/coursework evidence. For the MIS-to-Business-Analyst profile, gaps such as Power BI, Agile, Tableau, and KPIs aligned with missing or weak explicit resume evidence and recurring job-posting skills. For the Project Manager profile, risk management, Jira, and scope gaps aligned with project-management postings and the resume's stronger coursework evidence than tool or risk evidence. For the hybrid profile, risk management, milestones, Tableau, and KPIs aligned with combined delivery and analytics market signals.

The current evidence is appropriate for a class MVP because it demonstrates that the workflow works, outputs are grounded in retrieved postings, and recommendations change by target profile. However, the final report should avoid overstating these results. The test set is small, the job-posting corpus is local and directional, and ratings such as roadmap relevance are team smoke-review metrics rather than broad user-study findings.

Additional final validation should include:

- Re-running tests immediately before recording.
- Confirming the screenshot set matches `docs/demo_flow.md`.
- Verifying Docker build/run if Docker is available.
- Asking at least one teammate to independently rate roadmap and interview relevance if time allows.

## 7. Ethics And Responsible AI

CareerCompass handles career guidance, resume text, and labor-market evidence, so responsible-AI controls are central to the project. The main risks are resume privacy, bias in job-posting data, resume homogenization, overconfidence, and unequal access to recommended resources.

Resume privacy is the first risk. Resumes can include names, emails, phone numbers, employers, education history, and personal career goals. The MVP does not intentionally persist uploaded resume files or resume text. Resume content is used in the active Streamlit session. The final report should state that a production version should not store resumes unless users explicitly consent. A production system should also provide deletion controls and clear data-retention language.

Bias in job-posting data is another major risk. Job postings can overrepresent certain industries, regions, companies, credentials, and language patterns. The current local corpus is especially limited because it is a small directional sample. CareerCompass mitigates this by showing retrieved evidence, documenting data limitations, displaying confidence scores, and recommending advisor review. A production version should diversify data sources and evaluate recommendations across majors, roles, geographies, and demographic groups.

Resume homogenization is a risk because aggressive keyword optimization can make students sound generic or encourage exaggerated claims. CareerCompass mitigates this by preserving original evidence and keeping the resume draft editable. Resume suggestions should add market-aligned framing without inventing credentials, employers, tools, or outcomes. The app should continue to warn students that they must review and edit generated bullets before submitting applications.

Overconfidence is also important. Students may treat AI recommendations as definitive. CareerCompass addresses this by framing the final report as decision support rather than a guarantee. The app includes advisor-review language and confidence scores. The final submission should avoid language like "guaranteed match" or "must do." Recommendations should remain prioritized suggestions.

Access and equity must also be considered. Recommended learning resources may require paid subscriptions, specific software, or institutional access. The MVP includes free or commonly available resources when possible, and portfolio ideas can use public datasets and free dashboard tools. A production version should label free versus paid resources and include alternatives for students without access to paid certifications.

Overall, the responsible-AI position is that CareerCompass augments career advising rather than replacing it. It helps students prepare better questions, identify evidence gaps, and organize next actions, but it should remain transparent about uncertainty and data limitations.

## 8. Deployment And Containerization

CareerCompass can run locally through Streamlit or in Docker. Local development uses the Anaconda Python command:

```powershell
C:\Users\knolo\anaconda3\python.exe -m streamlit run app.py --server.port 8503
```

The local app opens at:

```text
http://localhost:8503
```

The project also includes a Dockerfile and deployment notes. The Docker build command is:

```powershell
docker build -t careercompass .
```

The Docker run command is:

```powershell
docker run --rm -p 8501:8501 careercompass
```

The Dockerized app opens at:

```text
http://localhost:8501
```

Docker was verified after Docker Desktop and required Windows virtualization features were installed. The recorded handoff states that `docker build -t careercompass .` passed, `docker run --rm -d -p 8501:8501 --name careercompass-verify careercompass` started successfully, `Invoke-WebRequest http://localhost:8501` returned `200 OK`, and the verification container was stopped.

The deployment design supports deterministic fallback mode by default. This matters because the app can run in a classroom or grading environment without requiring API keys. Optional LLM mode can be added through environment variables and a valid OpenAI key, but the demo does not depend on it.

Before final submission, the team should ensure:

- README and deployment docs agree on canonical ports.
- Local Streamlit uses port `8503`.
- Docker uses port `8501`.
- Optional LLM environment variables are documented consistently.
- No secrets or API keys are committed.
- Runtime logs, virtual environments, cache folders, and temp folders are excluded.

## 9. Screenshot And Demo Evidence

The screenshot plan is documented in `docs/demo_flow.md`, and the current screenshot directory contains the expected artifacts:

- `docs/screenshots/01-inputs.png`: Career profile input screen.
- `docs/screenshots/02-dashboard.png`: Dashboard metrics, market demand, and skill gaps.
- `docs/screenshots/03-gap-deep-dive.png`: Start closing a gap panel.
- `docs/screenshots/04-roadmap.png`: 30/60/90-day roadmap.
- `docs/screenshots/05-resume.png`: Resume keyword targets and editable draft.
- `docs/screenshots/06-interview.png`: Interview simulation and answer evaluation.
- `docs/screenshots/07-final-report.png`: Final strategy report.
- `docs/screenshots/08-agent-trace.png`: Technical demo notes with handoffs and confidence scores.
- `docs/screenshots/09-rubric-evidence.png`: Rubric Evidence view with requirement coverage and Responsible AI controls.

These images should be referenced in the final report or appendix rather than embedded at full size unless the submission format requires it. If the team records a final video after UI changes, the screenshots should be recaptured to match the final app state.

The demo flow supports a 5- to 7-minute presentation:

1. Problem and use case.
2. Inputs and agent architecture.
3. Dashboard and skill gaps.
4. Roadmap and resume optimization.
5. Interview simulation.
6. Final report, ethics, and evaluation evidence.
7. Rubric evidence and closing impact statement.

The video and report should describe the same agent flow and demo scenario to avoid confusing reviewers.

## 10. Limitations And Future Work

The most important limitation is the size and representativeness of the current job-posting data. The local retrieval corpus is useful for deterministic demo behavior, but it is not a comprehensive labor-market dataset. Future work should replace or extend the local corpus with a larger dataset, add vector retrieval, and evaluate source diversity.

A second limitation is that the current evaluation is a small local smoke review. The results show that the system runs, produces plausible outputs, and meets latency goals, but they do not prove general effectiveness across students, universities, geographies, or roles. Future evaluation should include more profiles, independent reviewers, advisor feedback, and user studies.

A third limitation is that live LLM mode is scaffolded but not required for the demo. Deterministic fallbacks improve reliability, but a production product would likely use structured model calls for more nuanced synthesis and personalization. The team should continue to validate model outputs against strict schemas and preserve fallback behavior.

A fourth limitation is that CareerCompass does not include authentication, long-term user profiles, persistent resume storage, or an advisor dashboard. These were intentionally out of scope for the MVP. A production version would need role-based access, secure storage, retention controls, and user consent flows.

Future work should include:

- ChromaDB/vector-search RAG over a larger job-posting dataset.
- More diverse data sources beyond Bay Area tech samples.
- Advisor-facing review tools.
- Stronger resume authenticity checks.
- Free/paid labeling for learning resources.
- Expanded evaluation across majors, roles, and locations.
- Production data-retention controls.
- A polished deployment target beyond local Docker.

## 11. Conclusion

CareerCompass demonstrates a practical agentic AI system for personalized career strategy and skill development. It takes a realistic student problem, breaks it into specialist-agent tasks, grounds recommendations in retrieved job evidence, and returns a structured career plan with resume, roadmap, interview, and final-report outputs.

The project satisfies the core goals of the MVP build spec: multi-agent architecture, LangGraph-ready supervisor orchestration, RAG-based evidence grounding, business value for students and career centers, ethical safeguards, Docker deployment path, and measurable evaluation outputs. The current implementation is intentionally demo-safe, deterministic by default, and supported by tests and documentation.

The strongest final-report framing is that CareerCompass is a reliable class MVP and architecture proof, not a finished production labor-market platform. Its evaluation results are local smoke evidence, not statistically representative findings. Its job-posting data is directional, not authoritative. Its recommendations should be reviewed by human advisors. Those limitations do not weaken the project; they show that the team understands responsible system boundaries.

With final screenshots, video recording, and careful GitHub cleanup, CareerCompass is ready to be presented as a Track B agentic AI system that turns student career preparation into an evidence-grounded, actionable plan.

## Appendix A: Rubric Evidence Map

| Rubric area | Weight | Project evidence |
| --- | ---: | --- |
| Agent Architecture & Implementation | 35% | Supervisor workflow, five specialist agents, synthesis node, typed shared state, structured handoffs, OpenAI hook, deterministic fallbacks, and workflow tests. |
| Business Value & Relevance | 20% | Student and career-center use case; resume plus coursework plus target role becomes a practical 90-day career strategy. |
| Container & Deployment Strategy | 15% | Dockerfile, `.dockerignore`, deployment guide, local and Docker run commands, deterministic fallback mode, and optional LLM variables. |
| Ethical Consideration | 15% | Privacy notes, bias limitations, confidence scores, advisor-review language, resume authenticity safeguards, and responsible-AI audit panel. |
| Documentation & Presentation | 15% | README, build spec, architecture handoff, data notes, demo flow, video script, evaluation plan/results, ethics notes, deployment notes, screenshots, and rubric evidence map. |

## Appendix B: Key Source Documents

- `README.md`
- `CareerCompass_MVP_Build_Spec.md`
- `docs/ARCHITECTURE_HANDOFF.md`
- `docs/AGENT_LOGIC.md`
- `docs/data_notes.md`
- `docs/evaluation.md`
- `docs/evaluation_results.md`
- `docs/ethics.md`
- `docs/deployment.md`
- `docs/rubric_evidence.md`
- `docs/demo_flow.md`
- `docs/screenshots/`
