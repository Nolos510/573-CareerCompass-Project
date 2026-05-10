# CareerCompass Demo Flow

Use this sequence for screenshots and the final video. Keep the demo tight: 5 to 7 minutes is enough to show the business value and the agentic architecture.

## Setup

Run the Streamlit app:

```powershell
C:\Users\knolo\anaconda3\python.exe -m streamlit run app.py --server.port 8502
```

Open:

```text
http://localhost:8502
```

Keep Presenter mode enabled for recording. Turn it off only if you want cleaner screenshots without cues.

## Demo Path

1. **Landing and Inputs**
   - Show CareerCompass as a career strategy workspace, not a generic chatbot.
   - Point out resume upload or paste, target role, location, timeline, and coursework.
   - Use the default role: `Business Analyst or Project Manager`.

2. **Run Analysis**
   - Click **Run CareerCompass analysis**.
   - Narrate the workflow: Supervisor routes to Market, Gap, Curriculum, Resume, Interview, and Synthesis agents.

3. **Dashboard**
   - Show role readiness, priority gaps, keyword coverage, and interview readiness.
   - Show market demand and skill gap report.
   - Use **Start closing a gap** to demonstrate that recommendations become first steps.

4. **Roadmap**
   - Show the 30/60/90-day plan.
   - Emphasize that the timeline is based on days until the target hire date.

5. **Resume**
   - Show keyword targets.
   - Select a resume template.
   - Check one or two resume suggestions.
   - Click **Apply selected suggestions**.
   - Show editable draft and export buttons.

6. **Interview**
   - Choose a company such as Salesforce.
   - Pick a preset or custom scenario.
   - Generate scenario questions.
   - Type a short STAR answer and click **Evaluate my answer**.
   - Show score, feedback, and sample answer.

7. **Final Report**
   - Show the copyable strategy report.
   - Mention advisor review, privacy, and confidence safeguards.

8. **Action Checklist**
   - Show certification suggestions, resume evidence reminders, and portfolio proof ideas.
   - Close by explaining that this helps students leave with next actions, not just advice.

## Screenshots To Capture

Save screenshots in `docs/screenshots/`.

- `01-inputs.png`: Career profile input screen.
- `02-dashboard.png`: Dashboard metrics, market demand, and skill gaps.
- `03-gap-deep-dive.png`: Start closing a gap panel.
- `04-roadmap.png`: 30/60/90-day roadmap.
- `05-resume.png`: Resume keyword targets and editable draft.
- `06-interview.png`: Interview simulation and answer evaluation.
- `07-final-report.png`: Final strategy report.
- `08-agent-trace.png`: Technical demo notes with handoffs and confidence scores.

## Video Timing

- 0:00 to 0:45: Problem and use case.
- 0:45 to 1:30: Inputs and agent architecture.
- 1:30 to 2:45: Dashboard and skill gaps.
- 2:45 to 3:45: Roadmap and resume optimization.
- 3:45 to 4:45: Interview simulation.
- 4:45 to 5:30: Final report, ethics, and evaluation evidence.
- 5:30 to 6:00: Team implementation status and next steps.

