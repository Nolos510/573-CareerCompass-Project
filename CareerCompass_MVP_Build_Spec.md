# CareerCompass MVP Build Spec

## 1. MVP Goal

Build a working multi-agent CareerCompass demo that helps a student or recent graduate turn their resume, coursework, target role, and timeline into a personalized career strategy.

The MVP should prove the class project requirements:

- Agentic AI system with multiple specialized agents
- LangGraph supervisor orchestration
- RAG over job market data
- Business value for students and career centers
- Ethical safeguards and human review
- Containerized deployment path
- Measurable evaluation outputs

## 2. Demo Scenario

Primary demo user:

- Recent MIS graduate
- Target role: Business Analyst
- Target location: San Francisco Bay Area
- Timeline: 90 days
- Current profile: coursework in databases, business analytics, and project management; limited Tableau portfolio evidence

The final demo should show one clean path:

1. Student uploads or pastes resume text.
2. Student enters target role, location, and timeline.
3. Supervisor routes the request through the agent workflow.
4. Market Demand Agent retrieves job-market evidence.
5. Gap Analysis Agent identifies skill gaps.
6. Curriculum Agent creates a 30/60/90-day roadmap.
7. Resume Optimization Agent suggests improved bullet points and ATS keywords.
8. Interview Simulation Agent generates questions and feedback.
9. Supervisor synthesizes all outputs into a strategy report.

## 3. MVP Scope

### In Scope

- One end-to-end demo path for Business Analyst roles
- Resume text input or PDF text extraction
- Target role, location, and timeline inputs
- RAG retrieval from job posting dataset
- JSON-style intermediate outputs between agents
- Final strategy dashboard
- Exportable or copyable strategy report
- Basic Docker setup
- Evaluation table for at least 3 sample profiles
- Ethics and privacy explanation

### Out of Scope

- Full user authentication
- Real LinkedIn or Indeed API integration
- Persistent resume storage
- Advanced advisor dashboard
- Production-grade authorization
- Multiple polished design themes
- Large-scale live scraping

## 4. System Architecture

Recommended workflow:

```text
START
  -> Supervisor
  -> MarketDemandAgent
  -> GapAnalysisAgent
  -> CurriculumAgent
  -> ResumeOptimizationAgent
  -> InterviewSimulationAgent
  -> SynthesisNode
END
```

Conditional paths:

- If the user only requests resume help, skip Curriculum Agent and Interview Agent.
- If no major gaps are found, Curriculum Agent returns reinforcement resources rather than a gap-heavy roadmap.
- If job data retrieval has low confidence, the final report flags low market-data confidence.

Shared state fields:

```text
user_profile
target_role
target_location
timeline_days
resume_text
coursework
retrieved_job_postings
market_skills
gap_report
learning_roadmap
resume_recommendations
interview_questions
interview_feedback
confidence_scores
final_strategy_report
```

## 5. Agent Responsibilities

### Supervisor Agent

Purpose:

- Validate inputs
- Route work through the LangGraph workflow
- Decide whether to run all agents or a subset
- Combine agent outputs into the final report

Output:

- Final career strategy summary
- Confidence notes
- Human advisor review disclaimer

### Market Demand Agent

Purpose:

- Retrieve relevant job postings using RAG
- Identify required skills, tools, qualifications, and recurring keywords
- Ground recommendations in job-market evidence

Output:

- Top market skills
- Frequency or importance notes
- Representative job-posting snippets or metadata

### Gap Analysis Agent

Purpose:

- Compare resume/coursework skills against market demand
- Assign gap severity
- Estimate role readiness percentage

Output:

- Skill gap table
- Severity: High, Medium, Low
- Evidence from resume and job postings
- Match percentage

### Curriculum Agent

Purpose:

- Convert gaps into learning actions
- Recommend realistic resources and projects
- Build a timeline-aligned roadmap

Output:

- 30/60/90-day roadmap
- Recommended courses, tutorials, certifications, or projects
- Relevance scores

### Resume Optimization Agent

Purpose:

- Suggest targeted resume improvements
- Add market-aligned keywords naturally
- Preserve the student's authentic experience

Output:

- Before/after bullet suggestions
- ATS keyword match notes
- Missing evidence suggestions

### Interview Simulation Agent

Purpose:

- Generate role-specific behavioral and technical interview questions
- Score sample responses using a rubric
- Give actionable feedback

Output:

- Interview questions
- STAR-format feedback
- Score and improvement notes

## 6. UI Screens

Use the Figma wireframes as the MVP screen map:

1. Upload and Profile Setup
2. Agent Progress View
3. Strategy Dashboard
4. Roadmap View
5. Resume Optimization
6. Interview Simulation

Recommended first implementation:

- Streamlit if the team wants fastest implementation
- Gradio if the team wants a simpler demo-first interface

## 7. Team Task Board

### Person 1: Team Lead / Architect

Owns:

- LangGraph workflow
- Shared AgentState schema
- Supervisor routing logic
- Integration checkpoints

Tasks:

- Define AgentState TypedDict
- Implement graph nodes and conditional edges
- Create one end-to-end integration test
- Maintain architecture diagram for final report

Done when:

- A single function can run the full workflow from sample input to final report.

### Person 2: Data and RAG Engineer

Owns:

- Job posting dataset
- Embeddings
- ChromaDB vector store
- Retrieval quality

Tasks:

- Clean and normalize job postings
- Add metadata: role, company, location, date
- Implement top-k retrieval
- Provide retrieved context to Market Demand Agent
- Document dataset limits and bias risks

Done when:

- Querying "Business Analyst San Francisco" returns relevant job-posting context.

### Person 3: Agent Developer

Owns:

- Gap Analysis Agent
- Curriculum Agent
- Resume Optimization Agent
- Interview Simulation Agent

Tasks:

- Finalize agent prompt templates
- Standardize JSON outputs
- Finish resume bullet rewrite logic
- Finish interview scoring rubric
- Add failure handling for missing or weak inputs

Done when:

- Each agent returns stable, structured output for the demo scenario.

### Person 4: Frontend and Demo Builder

Owns:

- Streamlit or Gradio UI
- User flow
- Demo polish
- Report export

Tasks:

- Build input screen
- Add agent progress states
- Display skill gap table
- Display roadmap, resume suggestions, and interview output
- Add export/copy final report button

Done when:

- A non-technical viewer can follow the full demo without reading code.

### Person 5: Evaluation, Ethics, and Deployment Lead

Owns:

- Metrics
- Docker
- Ethics section
- Final submission checklist

Tasks:

- Create evaluation matrix for 3 sample profiles
- Measure latency for full analysis
- Evaluate skill gap accuracy manually against retrieved postings
- Write privacy, bias, overconfidence, and resume homogenization mitigations
- Create Dockerfile and run instructions

Done when:

- The final report has evidence tables, ethics analysis, and deployment instructions.

## 8. Evaluation Plan

Track these metrics:

| Metric | Target | Evidence |
| --- | --- | --- |
| End-to-end latency | Under 30 seconds for demo profile | Timed test run |
| Skill gap accuracy | At least 80 percent agreement with manual review | Compare agent gaps to job-posting evidence |
| Resource relevance | Average rating 4 out of 5 | Team review or user test |
| ATS keyword lift | Improved keyword coverage after optimization | Before/after keyword count |
| Interview relevance | Average rating 4 out of 5 | Compare questions to target role |
| Output groundedness | No unsupported major recommendations | Check against retrieved postings |

## 9. Ethics and Risk Controls

Key risks:

- Job-posting data may overrepresent certain companies, regions, or industries.
- Resume optimization can make student resumes sound generic.
- Students may over-trust recommendations.
- Resumes contain sensitive personal data.
- AI feedback may reinforce biased hiring language.

Mitigations:

- Document dataset composition and limitations.
- Preserve original resume voice and flag uncertain rewrites.
- Include confidence scores and advisor review disclaimer.
- Avoid storing resumes after session completion.
- Review outputs for biased or exclusionary recommendations.

## 10. Week 12-16 Checklist

### Week 12

- Finish Resume Optimization Agent
- Finish Interview Simulation Agent scoring
- Extend RAG context to resume examples or role-specific examples

### Week 13

- Build Streamlit or Gradio UI
- Connect UI to supervisor workflow
- Add Dockerfile and environment setup

### Week 14

- Run evaluation on 3 sample profiles
- Fix weak outputs and prompt failures
- Start final report structure

### Week 15

- Finalize ethics section
- Record demo dry run
- Finish deployment instructions

### Week 16

- Submit final report, GitHub repository, Docker package, and 5-minute video demo

## 11. Final Demo Script

Recommended 5-minute structure:

1. Problem and business value: 30 seconds
2. Architecture and agent roles: 45 seconds
3. Live demo input setup: 45 seconds
4. Agent progress and results: 90 seconds
5. Resume and interview outputs: 60 seconds
6. Evaluation, ethics, and deployment: 60 seconds
7. Closing impact statement: 30 seconds

## 12. Immediate Next Actions

1. Confirm Streamlit or Gradio.
2. Pick the exact sample resume used in the final demo.
3. Freeze the MVP scenario to Business Analyst in San Francisco.
4. Assign the five ownership lanes.
5. Create the first end-to-end integration run before polishing individual screens.
