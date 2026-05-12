# CareerCompass Evaluation Results

Measured locally on 2026-05-11 using:

```powershell
C:\Users\knolo\anaconda3\python.exe
```

The app was evaluated in deterministic fallback mode so the demo does not depend on API keys, network access, or live model availability.

## Latency Smoke Test

Profile: MIS graduate targeting Business Analyst roles in the San Francisco Bay Area.

| Run | Latency seconds | Match | Keyword coverage | Retrieved postings |
| --- | ---: | ---: | ---: | ---: |
| 1 | 2.1936 | 38% | 50% | 5 |
| 2 | 0.0148 | 38% | 50% | 5 |
| 3 | 0.0137 | 38% | 50% | 5 |
| 4 | 0.0148 | 38% | 50% | 5 |
| 5 | 0.0141 | 38% | 50% | 5 |

Average latency: 0.4502 seconds.
Maximum observed latency: 2.1936 seconds.

Result: passes the under-30-second demo target.

## Three-Profile Smoke Evaluation

| Profile | Match | Keyword coverage | Retrieved postings | Gap distribution | Roadmap relevance average | Interview questions | Agent route |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| MIS to Business Analyst | 38% | 50% | 5 | 4 high, 0 medium, 4 low | 4.3/5 | 3 | supervisor -> market_demand -> gap_analysis -> curriculum -> resume_optimization -> interview_simulation -> synthesis |
| MIS to Project Manager | 61% | 62% | 5 | 1 high, 2 medium, 5 low | 4.3/5 | 3 | supervisor -> market_demand -> gap_analysis -> curriculum -> resume_optimization -> interview_simulation -> synthesis |
| Hybrid BA / PM | 46% | 50% | 5 | 2 high, 2 medium, 4 low | 4.3/5 | 3 | supervisor -> market_demand -> gap_analysis -> curriculum -> resume_optimization -> interview_simulation -> synthesis |

## Manual Agreement Notes

Manual review compared high and medium gaps against retrieved market skills and resume/coursework evidence.

| Profile | High/medium gaps reviewed | Agreement note |
| --- | --- | --- |
| MIS to Business Analyst | Power BI, Agile, Tableau, KPIs | Gaps align with missing or weak explicit resume evidence and recurring job-posting skills. |
| MIS to Project Manager | risk management, Jira, scope | Gaps align with PM postings and the resume's stronger coursework evidence than tool/risk evidence. |
| Hybrid BA / PM | risk management, milestones, Tableau, KPIs | Gaps align with hybrid delivery-plus-analytics market signals. |

Result: acceptable for class demo evidence, but final report should describe this as a small manual smoke review rather than a statistically representative evaluation.

## Remaining Evaluation Work

- Capture the screenshot set listed in `docs/demo_flow.md`.
- Verify Docker build/run immediately before final submission.
- If time permits, have at least one teammate independently rate roadmap and interview relevance.
- Treat the local job-posting corpus as directional until the ChromaDB/Kaggle RAG lane is integrated.
