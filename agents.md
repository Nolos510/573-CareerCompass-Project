# CareerCompass Inter-Agent Context

Last updated: 2026-05-10 by Codex in `C:\Users\knolo\OneDrive\Documents\New project`

This file is the shared memory layer for project agents. Read it at the beginning of any large context window and update it at the end with durable facts, decisions, changed files, tests, blockers, and handoff notes. Keep it concise and useful; do not paste full chat transcripts, secrets, or throwaway reasoning.

## Context Coverage

This first version consolidates the visible repository state, root docs, and the current Codex thread. It does not include other chat windows unless their outcomes were saved into the repo. Future agents should append or revise this file whenever they learn something durable in another context window.

## Agent Start Protocol

At the beginning of a large task:

1. Read this file first.
2. Before doing any report, cleanup, commit, pull, rebase, merge, or push work, check the live remote `main` branch and compare it against the local branch. Do not assume the local `origin/main` ref is current unless it was just fetched or checked.
3. Check `git status --short --branch`.
4. Read the relevant lane docs before editing: `README.md`, `docs/ARCHITECTURE_HANDOFF.md`, `docs/CAREERCOMPASS_TEAM_DEV_SPLIT.md`, and any lane-specific doc.
5. Identify the lane you are touching and avoid unrelated refactors.
6. Preserve existing user or teammate changes. Do not reset, checkout, or overwrite work you did not create.

## Agent End Protocol

Before ending a large task:

1. Update this file if anything durable changed.
2. Add a handoff entry with date, agent/window, changed files, tests run, and open questions.
3. Mention any skipped verification and why.
4. Keep the update factual and brief enough for the next agent to scan.

## Project Snapshot

Project: `573-CareerCompass-Project`

Goal: Build a working multi-agent CareerCompass MVP that helps a student or recent graduate convert resume text, coursework, target role, target location, and timeline into a personalized career strategy.

Primary demo scenario:

- Recent MIS graduate.
- Target: Business Analyst or Project Manager style roles.
- Location: San Francisco Bay Area.
- Timeline: 90 days.
- Current profile: databases, business analytics, project management coursework, limited Tableau portfolio evidence.

Current implementation:

- Streamlit MVP in `app.py`.
- Python package in `careercompass/`.
- Deterministic demo-safe behavior by default.
- Optional OpenAI-backed structured model calls through `careercompass/llm_client.py`.
- Local lexical RAG over `careercompass/data/job_postings.json`.
- Docker and class-deliverable docs exist.

## Current Runtime Notes

Run locally:

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

Machine-specific command from `README.md`:

```powershell
C:\Users\knolo\anaconda3\python.exe -m streamlit run app.py --server.port 8503
```

`docs/demo_flow.md` also mentions port `8502`, so verify the active port before recording or browser testing.

Optional live LLM mode:

```powershell
$env:CAREERCOMPASS_LLM_ENABLED="true"
$env:OPENAI_API_KEY="<secret>"
$env:CAREERCOMPASS_OPENAI_MODEL="gpt-5.4-mini"
```

Do not hardcode API keys. If model calls fail, the app should sanitize the error, append it to `state["errors"]`, and fall back to deterministic outputs.

## Architecture Snapshot

Primary workflow:

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

Important contracts:

- `careercompass/state.py` defines `AgentState`, `AgentHandoff`, `CareerStrategyOutput`, `AgentName`, and `WorkflowIntent`.
- `careercompass/agents.py` owns workflow orchestration and Streamlit-facing output assembly.
- `run_career_analysis()` returns contract version `careercompass.strategy.v1`.
- `validate_final_output()` verifies required UI fields, version, trace shape, and empty handoff queue.
- If `langgraph` is installed, `build_supervisor_workflow()` compiles a LangGraph `StateGraph`; otherwise `DeterministicCareerWorkflow` follows the same route for reliable demos.

## Lane Ownership

Team lanes from `docs/CAREERCOMPASS_TEAM_DEV_SPLIT.md`:

| Lane | Owner | Branch Pattern | Owns |
| --- | --- | --- | --- |
| Architecture / Integration | Carlo | `carlo-architecture-*` | LangGraph supervisor, shared state, integration |
| RAG / Data | Nhi | `nhi-rag-data-*` | job postings, ChromaDB/vector search, retrieved evidence |
| Agent Logic | TM3 | `tm3-agent-logic-*` | prompts, JSON outputs, fallbacks, validation |
| Frontend / Demo | TM4 | `tm4-frontend-demo-*` | Streamlit polish, screenshots, video flow |
| Evaluation / Deployment | TM5 | `tm5-eval-deploy-*` | Docker, metrics, ethics, report support |

Shared files that need extra coordination:

```text
README.md
app.py
requirements.txt
careercompass/agents.py
CareerCompass_MVP_Build_Spec.md
```

## File Map

Core app:

- `app.py`: Streamlit UI and demo flow.
- `careercompass/agents.py`: supervisor/workflow nodes and final output assembly.
- `careercompass/state.py`: shared workflow state and output contracts.
- `careercompass/rag.py`: deterministic lexical retrieval over local job postings.
- `careercompass/data/job_postings.json`: lightweight local demo corpus.
- `careercompass/agent_logic.py`: model-call hook plus validation/fallback selection.
- `careercompass/prompts.py`: prompt templates and JSON output instructions.
- `careercompass/schemas.py`: strict structured output schemas.
- `careercompass/fallbacks.py`: deterministic agent outputs for demos and failures.
- `careercompass/llm_client.py`: optional OpenAI Responses API wrapper.
- `careercompass/demo_data.py`: default demo profile data.

Tests:

- `tests/test_workflow.py`: workflow and compiled graph regression tests.
- `tests/test_agent_logic.py`: structured model call and fallback behavior.
- `tests/test_rag.py`: local retrieval behavior.
- `tests/test_project_artifacts.py`: project artifact expectations.

Docs:

- `docs/ARCHITECTURE_HANDOFF.md`: architecture lane summary.
- `docs/AGENT_LOGIC.md`: TM3 prompts/model/fallback notes.
- `docs/data_notes.md`: current local dataset and RAG upgrade plan.
- `docs/demo_flow.md`: demo and screenshot sequence.
- `docs/demo_script.md`: video script.
- `docs/evaluation.md`: metrics and test profiles.
- `docs/ethics.md`: privacy, bias, overconfidence, and access risks.
- `docs/deployment.md`: deployment notes.
- `docs/BRANCH_RULES.md`, `docs/GIT_SYNC_WORKFLOW.md`, `docs/GROUP_PROJECT_SOP_TEMPLATE.md`: repo workflow governance.

## RAG And Data State

Current RAG is deterministic and local:

1. Tokenize target role and location.
2. Score postings by role, location, and skill overlap.
3. Return top postings with retrieval scores and evidence summaries.
4. Derive market skills from retrieved postings.

Keep the retrieved posting shape stable when upgrading to ChromaDB/vector search:

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

Known limitation: the current local sample is directional, not representative of the full labor market. Final deliverables should state this clearly.

## Agent Logic State

Structured output areas:

- `market_skills`
- `gap_report`
- `learning_roadmap`
- `resume_recommendations`
- `interview_questions`
- `final_strategy_report`
- `route_plan`

Fallback behavior should trigger when:

- No API key is present.
- LLM use is disabled.
- OpenAI SDK is unavailable.
- API call fails.
- Model output is empty, invalid JSON, refusal-like, or schema-invalid.

Open question from `docs/AGENT_LOGIC.md`: should synthesis eventually use live structured model output, or remain deterministic for demo stability?

## Demo And Evaluation State

Demo path:

1. Inputs: resume paste/upload, role, location, timeline, coursework.
2. Run CareerCompass analysis.
3. Dashboard: readiness, gaps, keyword coverage, interview readiness.
4. Roadmap: 30/60/90 plan.
5. Resume: keyword targets, selectable suggestions, editable draft, export/copy.
6. Interview: company/scenario questions, STAR answer evaluation.
7. Final report: copyable strategy with safeguards.
8. Technical evidence: trace, handoffs, confidence, metrics.

Evaluation targets:

- End-to-end latency under 30 seconds.
- Skill gap accuracy at least 80 percent manual agreement.
- Resume keyword coverage improves after optimization.
- Learning resource relevance average 4/5.
- Interview relevance average 4/5.
- At least 3 relevant postings for common demo roles.

Test profiles should include MIS to Business Analyst, MIS to Project Manager, and hybrid Business Analyst / Project Manager.

## Ethics And Safety Notes

Current mitigations:

- Resume uploads/text are not intentionally persisted by the MVP.
- Retrieved evidence is visible to users.
- Confidence scores and advisor-review language are included.
- Resume suggestions should preserve original evidence and avoid inventing claims.
- Resource recommendations should consider free or commonly available options.

Future production notes:

- Add explicit retention/deletion controls before storing resumes.
- Diversify job data beyond Bay Area tech samples.
- Evaluate recommendations across majors, roles, and geographies.
- Label free versus paid resources.

## Current Git And Workspace State

Observed on 2026-05-10:

- Root repo branch: `main...origin/main`.
- Recent commit: `0713775 Make recommendations respond to selected profile`.
- Root repo has untracked local directories:
  - `careercompass-dynamic-ui-worktree/`
  - `careercompass-latest-main-view/`
  - `tm4-frontend-demo-polish-worktree/`
- `git worktree list` only reports the root path, so treat these nested directories carefully; at least some behave like copied/nested working directories rather than registered worktrees.
- `tm4-frontend-demo-polish-worktree/` is on branch `tm4-frontend-demo-polish...origin/tm4-frontend-demo-polish` and has many modified/added/deleted files. Do not delete or overwrite it without explicit user permission.
- `careercompass-dynamic-ui-worktree/` appears clean on `main...origin/main`.
- `careercompass-latest-main-view/` is not an independent git worktree from the root status perspective; commands inside it report parent/root changes.
- `rg` failed with `Access is denied` in this environment; use PowerShell fallback commands if needed.

## Open Questions And Watch Items

- Which Streamlit port should be canonical for demos: `8502` or `8503`?
- Should final synthesis use live LLM output or remain deterministic for class-demo stability?
- Should nested worktree/copy directories be moved outside the root repo or added to `.gitignore`?
- Has the latest TM4 frontend polish branch been merged, abandoned, or superseded by `main`?
- Need CodeRabbit or equivalent review for agent-logic/security-sensitive changes before final merge.
- Need final screenshot set under `docs/screenshots/` before recording.

## Handoff Log

### 2026-05-10 - Codex - Created inter-agent context file

Context gathered:

- Read `README.md`, `CareerCompass_MVP_Build_Spec.md`, `docs/ARCHITECTURE_HANDOFF.md`, `docs/AGENT_LOGIC.md`, `docs/CAREERCOMPASS_TEAM_DEV_SPLIT.md`, `docs/data_notes.md`, `docs/demo_flow.md`, `docs/evaluation.md`, and `docs/ethics.md`.
- Inspected top-level repo contents, `careercompass/`, `tests/`, recent git log, and nested worktree/copy directory status.

Changed files:

- Added `agents.md`.

Verification:

- No code behavior changed.
- No tests run because this is a documentation/context file.

Notes for next agent:

- Treat this file as living memory. Update it at the end of any substantial project session.
- If you have access to another project chat, summarize only durable decisions and paste them here.

### 2026-05-11 - Codex - Implemented rubric readiness pass

Changed files:

- Added `pytest.ini` so plain `pytest` only collects root `tests/` and ignores nested local workspace copies.
- Updated `.gitignore` and `.dockerignore` to exclude nested local workspace directories from git noise and Docker build context.
- Updated `app.py` with a visible Rubric Evidence view, Responsible AI / advisor review audit, and compact agent coordination evidence table.
- Fixed the Streamlit team status panel so it uses native components instead of leaking raw HTML.
- Standardized demo docs on port `8503`.
- Added `docs/evaluation_results.md` and `docs/rubric_evidence.md`; updated `docs/evaluation.md`, `docs/data_notes.md`, and `docs/demo_flow.md`.
- Captured screenshots under `docs/screenshots/01-inputs.png` through `docs/screenshots/09-rubric-evidence.png`.
- Updated `tests/test_project_artifacts.py` to cover evaluation/rubric docs and pytest config.

Verification:

- `C:\Users\knolo\anaconda3\python.exe -m pytest -q` -> 34 passed, 1 LangGraph deprecation warning.
- `C:\Users\knolo\anaconda3\python.exe -m compileall app.py careercompass tests` -> passed.
- Local evaluation smoke run recorded 5 latency runs and 3 profile runs in `docs/evaluation_results.md`.
- Streamlit screenshot capture completed with headless Playwright after installing the local Chromium browser binary.

Skipped verification:

- Docker build/run was not verified because `docker` is not installed or not on PATH in this shell. The Dockerfile and deployment docs remain in place for a machine with Docker Desktop.

### 2026-05-12 - Codex - Attempted Docker verification

Changed files:

- Updated `agents.md` with this deployment verification handoff.

Verification:

- `docker --version` -> failed because `docker` is not recognized in this PowerShell environment.
- Checked standard Docker Desktop CLI path `C:\Program Files\Docker\Docker\resources\bin\docker.exe` -> not present.
- `docker build -t careercompass .` -> failed because `docker` is not recognized.

Skipped verification:

- `docker run --rm -p 8501:8501 careercompass` was not run because the image could not be built without a Docker CLI/daemon on this machine.

Notes for next agent:

- Run the documented Docker commands on a machine with Docker Desktop installed and running, then update this handoff with the build/run result.

### 2026-05-12 - Codex - Installed Docker Desktop, WSL admin step pending

Changed files:

- Updated `agents.md` with this Docker install handoff.

Verification:

- Downloaded Docker Desktop from Docker's official Windows installer URL and ran per-user install with `install --user --quiet --accept-license`.
- Docker install log reports version `4.73.0 (226246)` and `Installation succeeded`.
- Direct CLI check with `C:\Users\knolo\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe --version` -> `Docker version 29.4.3, build 055a478`.
- Docker Desktop processes started, but `docker info` reports `Docker Desktop is unable to start`.
- `wsl --status` reports WSL is not installed.
- `wsl --install --no-distribution` and `wsl.exe --install --web-download --no-distribution` both failed because WSL is not installed/enabled.
- `dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart` and `dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart` failed with `Error: 740`, meaning elevated Administrator permissions are required.

Skipped verification:

- `docker build -t careercompass .` and `docker run --rm -p 8501:8501 careercompass` still need to be rerun after WSL/Virtual Machine Platform are enabled and Windows has restarted if prompted.

Notes for next agent:

- Open PowerShell as Administrator and run:

```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
wsl --install --no-distribution
```

- Restart Windows if prompted, launch Docker Desktop, then retry the Docker build/run verification.

### 2026-05-12 - Codex - Completed Docker install and verification

Changed files:

- Updated `agents.md` with this successful Docker verification handoff.

Verification:

- Elevated PowerShell enabled `Microsoft-Windows-Subsystem-Linux` and `VirtualMachinePlatform`.
- Elevated status check confirmed both Windows optional features are `Enabled`.
- Restarted Docker Desktop without requiring a full Windows reboot in this session.
- `docker info --format '{{.ServerVersion}} {{.OperatingSystem}}'` -> `29.4.3 Docker Desktop`.
- `docker build -t careercompass .` -> passed after adding Docker Desktop's `resources\bin` directory to this shell's PATH.
- `docker run --rm -d -p 8501:8501 --name careercompass-verify careercompass` -> started container `d976a6de8fdbc500640a7e36186645d6a80727e7d723e0c023dd44c1d30235fd`.
- `Invoke-WebRequest http://localhost:8501` -> `200 OK`.
- Container logs showed Streamlit serving at `http://localhost:8501`.
- Stopped the temporary `careercompass-verify` container after verification.

Notes for next agent:

- If a new terminal cannot find `docker`, open a fresh PowerShell window or add `C:\Users\knolo\AppData\Local\Programs\DockerDesktop\resources\bin` to PATH for that session.

### 2026-05-12 - Codex - Restyled Streamlit dashboard experience

Changed files:

- Updated `app.py` with a custom CareerCompass command-center visual system: richer hero, dark sidebar styling, section headers, signal metric cards, agent pipeline cards, next-action cards, roadmap cards, and tighter form/table/button styling.
- Preserved existing workflow contracts and deterministic analysis behavior.
- Updated `agents.md` with this UI handoff.

Verification:

- Reviewed Creative Tim dashboard template article for dashboard-pattern inspiration, especially modular components, material/soft UI systems, and gradient/admin dashboard patterns.
- `C:\Users\knolo\anaconda3\python.exe -m compileall app.py careercompass tests` -> passed.
- `C:\Users\knolo\anaconda3\python.exe -m pytest -q` -> 34 passed, 1 LangGraph deprecation warning.
- `streamlit.testing.v1.AppTest.from_file("app.py").run(timeout=30)` -> 0 Streamlit exceptions; the Anaconda temp-directory cleanup emitted a Windows `PermissionError` after the successful run.
- Timed foreground Streamlit run served `http://localhost:8503/?demo_autorun=1` with `200 OK`.

Skipped verification:

- In-app Browser automation could not be used because the Node REPL backend returned `Access is denied`.
- `npx` and Python `playwright` are not available in this shell.
- Headless Chrome/Edge screenshot commands exited without writing screenshots, so updated demo screenshots still need to be recaptured manually or from a browser-enabled environment.

### 2026-05-12 - Codex - QA pass for refreshed UI

Changed files:

- Updated `app.py` to scope the large hero `h1` styling away from the Streamlit sidebar title, keeping the sidebar compact after the visual refresh.
- Updated `agents.md` with this QA handoff.

Verification:

- `C:\Users\knolo\anaconda3\python.exe -m compileall app.py careercompass tests` -> passed.
- Streamlit AppTest initial load -> 0 exceptions.
- Streamlit AppTest after clicking `Run CareerCompass analysis` -> 0 exceptions and workspace tabs rendered.
- Streamlit AppTest visited `Dashboard`, `Roadmap`, `Resume`, `Interview`, `Final Report`, `Action Checklist`, and `Rubric Evidence` -> 0 exceptions in every view.
- Streamlit AppTest resume interaction checked one suggestion and clicked `Apply selected suggestions` -> editable draft contained `APPLIED CAREERCOMPASS IMPROVEMENTS`.
- Streamlit AppTest interview interaction generated scenario questions, filled a STAR-style answer, clicked `Evaluate my answer` -> `Evaluation` state rendered.
- Timed foreground Streamlit server served `http://localhost:8503/?demo_autorun=1&demo_view=dashboard` -> `200 OK`.
- `C:\Users\knolo\anaconda3\python.exe -m pytest -q` -> 34 passed, 1 LangGraph deprecation warning.
- `git diff --check -- app.py agents.md` -> passed except expected LF-to-CRLF warning for `app.py`.

Skipped verification:

- Browser plugin rendered screenshot/console checks remain blocked because the Node REPL Browser backend returns `Access is denied`.

### 2026-05-12 - Codex - Fixed local Streamlit launch on port 8503

Changed files:

- Updated `run_streamlit.ps1` to use port `8503` instead of stale port `8502`.
- Adjusted `run_streamlit.ps1` so Streamlit stderr warnings do not stop the launcher before the server binds.
- Added `run_streamlit_8503.cmd` as a simple Windows launcher for the verified command.
- Updated `agents.md` with this launch handoff.

Verification:

- Launched `run_streamlit_8503.cmd` outside the sandbox so the server persists.
- `netstat -ano | Select-String ':8503'` -> showed `0.0.0.0:8503` and `[::]:8503` listening.
- `Invoke-WebRequest http://localhost:8503/` -> `200 OK`.

Notes:

- If Codex starts Streamlit inside the sandbox, background processes may be killed when the command returns. Use `run_streamlit_8503.cmd` or the documented Anaconda command from a normal terminal for a persistent local demo server.

### 2026-05-12 - Codex - Reverted custom dashboard redesign

Changed files:

- Reverted `app.py` away from the custom command-center UI and restored the simpler Streamlit-native layout, including the original hero, metric row, dataframe-first dashboard, native team status cards, and standard section headers.
- Kept the functional launcher fixes for port `8503`.
- Updated `agents.md` with this rollback handoff.

Verification:

- Confirmed no references remain to the removed custom render helpers or custom dashboard card classes.
- `C:\Users\knolo\anaconda3\python.exe -m compileall app.py` -> passed.
- Streamlit AppTest initial load -> 0 exceptions.
- Streamlit AppTest clicked `Run CareerCompass analysis` -> 0 exceptions and workspace tabs rendered.
- `C:\Users\knolo\anaconda3\python.exe -m pytest -q` -> 34 passed, 1 LangGraph deprecation warning.
- Existing server on `http://localhost:8503/?demo_autorun=1&demo_view=dashboard` -> `200 OK`.

Notes:

- The earlier redesign leaked raw custom HTML in the dashboard; this rollback removes that custom card layer.

### 2026-05-12 - Codex - Added final report draft and GitHub cleanup handoff

Changed files:

- Added `docs/final_report_draft.md` as an independent full report draft for the report teammate to compare against the official submission.
- Added `docs/github_cleanup_todo.md` as a careful GitHub cleanup checklist for another agent, with the first gate to read `agents.md` and check live remote `main` before any pull, commit, push, rebase, merge, or checkout work.
- Updated `agents.md` with this handoff.

Verification:

- Read `agents.md` before work.
- Checked repo state with `git status --short --branch`; local `main` remains behind remote with uncommitted local work.
- Checked local `HEAD`: `f94ede84dac41f9a983b6519743761fa86bd5e08`.
- Checked local `origin/main`: `e7ef80a87b7daada39f2981dc6beb265ab054c46`.
- Checked live remote `main` with `git ls-remote origin refs/heads/main`: `e7ef80a87b7daada39f2981dc6beb265ab054c46`.
- `C:\Users\knolo\anaconda3\python.exe -m pytest -q` -> 34 passed, 1 LangGraph deprecation warning.
- `C:\Users\knolo\anaconda3\python.exe -m compileall app.py careercompass tests` -> passed.
- `git diff --check -- docs\final_report_draft.md docs\github_cleanup_todo.md agents.md` -> passed.

Notes:

- No pull, fetch, rebase, merge, commit, reset, checkout, or push was performed.
- The report draft explicitly frames evaluation as local smoke evidence and manual review, not a statistically representative labor-market study.

### 2026-05-12 - Codex - Converted final report draft to Word

Changed files:

- Added `docs/final_report_draft.docx` as a Microsoft Word version of the independent final report draft.
- Added `.tmp/create_final_report_docx.py` as the local conversion helper used for this artifact.
- Updated `agents.md` with this handoff.

Verification:

- Read `agents.md` before work.
- Checked repo state with `git status --short --branch`; local `main` remains behind remote with uncommitted local work.
- Checked local `HEAD`: `f94ede84dac41f9a983b6519743761fa86bd5e08`.
- Checked local `origin/main`: `e7ef80a87b7daada39f2981dc6beb265ab054c46`.
- Checked live remote `main` with `git ls-remote origin refs/heads/main`: `e7ef80a87b7daada39f2981dc6beb265ab054c46`.
- Generated the Word document from `docs/final_report_draft.md` using the bundled Python runtime and `python-docx`.
- Structural DOCX validation passed: 172 paragraphs, 3 tables, 1 section, and title `CareerCompass Final Report Draft`.

Skipped verification:

- Visual DOCX render-to-PNG was not completed because LibreOffice/`soffice` is not installed, and no `winget`, `choco`, or `scoop` installer command is available in this shell.
- The render helper was retried outside the sandbox; after temp permissions were resolved, it failed only because the `soffice` executable was missing.

Notes:

- No pull, fetch, rebase, merge, commit, reset, checkout, or push was performed.

### 2026-05-12 - Codex - Protected final submission cleanup branch

Changed files:

- Created safety branch `codex/final-submission-cleanup` before syncing with remote main.
- Preserved the main cleanup work in commit `68cc134` (`Finalize submission evidence and demo polish`).
- Added final submission evidence/docs, rubric evidence docs, screenshots, test collection config, Streamlit launch helpers, Docker ignore/git ignore cleanup, and the Word report artifact already described in the previous handoff.
- Kept `.tmp/` helper scripts and runtime/cache noise out of staging.

Verification:

- Read `agents.md` before git operations and followed the non-destructive first-gate checks.
- Checked live remote `main` before preservation: `e7ef80a87b7daada39f2981dc6beb265ab054c46`.
- `C:\Users\knolo\anaconda3\python.exe -m pytest -q` -> 34 passed, 1 LangGraph deprecation warning.
- `C:\Users\knolo\anaconda3\python.exe -m compileall app.py careercompass tests` -> passed.
- Existing local Streamlit server on `http://localhost:8503/` -> `200 OK`.
- Docker Desktop CLI was available at `C:\Users\knolo\AppData\Local\Programs\DockerDesktop\resources\bin`; `docker build -t careercompass .` passed after adding that directory to PATH for the shell.
- Temporary Docker container `careercompass-cleanup-verify` served `http://localhost:8501/` with `200 OK` and was stopped after verification.

Notes:

- No pull, rebase, merge, reset, or force-push was performed before protecting local work.
- Local branch started from `f94ede8` and was behind live remote `main` by 12 commits, so this branch should be reviewed through a PR into `main`.
- The first cleanup commit was made with author `Nolos510 <knolos510@gmail.com>`.

### 2026-05-12 - Codex - Re-ran Docker build/run verification

Changed files:

- Updated `agents.md` with this fresh Docker verification handoff.

Verification:

- Read `agents.md` tail and checked `git status --short --branch`; working branch is `codex/final-submission-cleanup...origin/codex/final-submission-cleanup`.
- `docker info --format '{{.ServerVersion}} {{.OperatingSystem}}'` -> `29.4.3 Docker Desktop`.
- `docker build -t careercompass .` -> passed.
- Verified port `8501` was clear, then ran `docker run --rm -d -p 8501:8501 --name careercompass-verify careercompass`.
- Container `236a1244afba474f23499901446b1d732b8cb2345ee0f28fbd92534f9f2e6e05` started successfully.
- Container logs showed Streamlit serving on `http://localhost:8501`.
- `Invoke-WebRequest http://localhost:8501` -> `HTTP 200 OK`.
- Stopped the temporary `careercompass-verify` container after verification.
