# CareerCompass Demo Flow

## Goal

Show one clean end-to-end CareerCompass path for a recent MIS graduate targeting Business Analyst or Project Manager roles in the San Francisco Bay Area.

## Setup

- Run the app with `.\run_streamlit.ps1`.
- Open `http://localhost:8502`.
- Click **Reset sample demo profile** before recording or presenting.
- Keep the default target role, location, 90-day timeline, and coursework.

For repeatable screenshot capture, append `?demo_autorun=1&demo_view=dashboard` to auto-run the sample profile. Supported `demo_view` values are `dashboard`, `roadmap`, `resume`, `interview`, `report`, and `checklist`.

## Click Path

1. Confirm the profile setup screen shows the sample resume and Bay Area target.
2. Click **Run CareerCompass analysis**.
3. On **1. Dashboard**, explain role readiness, priority gaps, keyword coverage, and recommended next moves.
4. Use **Start closing a gap** to show why one gap matters, first steps, search terms, and resume proof.
5. Open the technical demo expander only if the audience needs architecture evidence.
6. Move to **2. Roadmap** and show the 30/60/90-day progression.
7. Move to **3. Resume**, show keyword targets, one before-and-after suggestion, and export options.
8. Move to **4. Interview**, generate scenario questions, select one question, and evaluate a short answer.
9. Move to **5. Final Report** and show the copyable strategy report plus advisor disclaimer.
10. Move to **6. Action Checklist** and close on student next steps.

## Expected Presenter Story

- CareerCompass starts with a student profile rather than a generic chatbot prompt.
- A supervisor workflow coordinates market demand, gap analysis, curriculum planning, resume optimization, interview simulation, and synthesis.
- The dashboard converts agent outputs into decisions the student can understand.
- The roadmap, resume, and interview screens show that the system gives actionable follow-through.
- The final report and disclaimer position the tool as decision support for students and career advisors.

## Fallbacks

- If upload parsing fails, paste the resume text directly.
- If the app reloads mid-demo, click **Reset sample demo profile** and run the analysis again.
- If interview evaluation receives an empty answer, use that to demonstrate guardrails and then enter a short STAR-style response.
- If optional PDF or DOCX packages are unavailable, use TXT input for the live walkthrough.
