# CareerCompass Evaluation Plan

This plan supports the final project report and video demo. The latest local smoke results are recorded in [evaluation_results.md](evaluation_results.md).

## Metrics

| Metric | Target | Current MVP Evidence | Next Validation Step |
| --- | --- | --- | --- |
| End-to-end latency | Under 30 seconds | Five local runs averaged 0.4502 seconds, max 2.1936 seconds. | Re-run before recording and report the latest value. |
| Skill gap accuracy | 80 percent manual agreement | Three-profile smoke review found high/medium gaps aligned with retrieved skills and profile evidence. | Have teammates independently review and sign off if time allows. |
| Resume keyword coverage | Increased keyword coverage after optimization | Resume view lists target keywords and suggested bullet rewrites; smoke profiles report coverage. | Capture before/after screenshots in the resume view. |
| Learning resource relevance | 4 out of 5 user rating | Three smoke profiles averaged 4.3/5 roadmap relevance. | Ask test users or teammates to rate final roadmap resources. |
| Interview question relevance | 4 out of 5 average relevance | Each smoke profile generated 3 role-specific questions. | Rate questions against target job descriptions before final report. |
| Retrieved evidence quality | At least 3 relevant postings for common demo roles | Each smoke profile returned 5 retrieved postings with evidence summaries. | Replace local dataset with ChromaDB top-k retrieval if the RAG lane is merged. |

## Test Profiles

Use at least three profiles:

- MIS student targeting Business Analyst roles.
- MIS student targeting Project Manager roles.
- Hybrid Business Analyst / Project Manager target.

Each profile should include:

- Resume text.
- Coursework list.
- Target role.
- Location.
- Timeline.

## Evaluation Procedure

1. Run CareerCompass for each test profile.
2. Save dashboard, skill gap, resume, interview, and final report screenshots.
3. Record latency from the technical demo panel.
4. Review retrieved job-posting evidence for relevance.
5. Compare skill gaps against the retrieved postings.
6. Rate roadmap and interview outputs using the metrics table.
7. Document limitations and disagreements in the final report.

## Acceptance Criteria For Final Demo

- Streamlit app runs locally or in Docker.
- Analysis completes under 30 seconds in the demo environment.
- Dashboard displays retrieved job evidence.
- Final report includes strategy, roadmap, resume, interview, and ethical safeguard language.
- Tests pass before recording.

