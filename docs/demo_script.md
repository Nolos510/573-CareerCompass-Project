# CareerCompass Video Script

## Opening

CareerCompass is an agentic AI system for students and recent graduates who are trying to turn their coursework, resume, and career interests into a focused job-search strategy.

The problem is that students often apply broadly and receive generic advice. CareerCompass gives them a specific, market-aligned plan: skill gaps, learning roadmap, resume improvements, interview practice, and a final career strategy report.

## Inputs

The student can paste a resume or upload a local resume file. Then they choose the target role, location, timeline, and relevant coursework.

For this demo, we are using a recent MIS graduate targeting Business Analyst or Project Manager roles in the San Francisco Bay Area.

## Architecture

This is Track B: an agentic AI system. The Supervisor Agent coordinates the workflow and routes state through five specialist agents:

- Market Demand Agent.
- Gap Analysis Agent.
- Curriculum Agent.
- Resume Optimization Agent.
- Interview Simulation Agent.

The agents share a typed state object, and the app records handoffs so we can show which agent produced which output.

## Dashboard

The dashboard summarizes role readiness, priority gaps, resume keyword coverage, and interview readiness.

The market demand section shows what skills are important for the target role. The skill gap report compares those skills against the student's resume and coursework evidence.

The key design choice is that recommendations do not stop at advice. The student can pick a gap, see why it matters, choose starter business cases, and get first steps for building proof.

## Roadmap

The roadmap turns the gaps into a 30/60/90-day plan. This is important because students need a sequence they can act on, not just a list of skills.

## Resume

The resume module recommends keywords, lets the student select a resume format, applies selected improvements, and creates an editable draft. The draft can be exported as text or DOCX.

We also designed this to avoid resume homogenization. The system should preserve the student's real experience and only add market-aligned language where it is accurate.

## Interview

The interview simulator creates role-specific questions. The student can choose a preset scenario, enter a company, or paste a custom scenario they received from an interview.

After the student answers, CareerCompass evaluates the response using a simple rubric and provides feedback plus a stronger sample answer.

## Final Report

The final report synthesizes the agent outputs into one student-facing strategy. This is where the Supervisor Agent creates a coherent plan from the specialist work.

The system also includes safeguards: confidence signals, advisor review language, and privacy assumptions around not storing resume data beyond the active session.

## Closing

CareerCompass demonstrates how agentic AI can make career advising more scalable and specific. The next implementation steps are RAG with job postings, stronger evaluation, Docker deployment, and final ethics documentation.

