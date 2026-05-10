# CareerCompass Data Notes

This is the first RAG/Data lane implementation.

## Current Dataset

The MVP can use the Kaggle LinkedIn Job Postings dataset when it has been downloaded locally:

```text
https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
```

Because the full Kaggle dataset is large and may require Kaggle authentication, the raw download is not committed to Git. Put the downloaded zip or extracted files under:

```text
data/raw/linkedin-job-postings/
```

Then prepare the MVP JSON:

```powershell
C:\Users\knolo\anaconda3\python.exe tools\prepare_linkedin_kaggle.py
```

This writes:

```text
data/processed/linkedin_job_postings_mvp.json
```

`careercompass/rag.py` automatically uses that processed file when it exists. If it does not exist, the app falls back to the tracked lightweight sample:

```text
careercompass/data/job_postings.json
```

The fallback sample lets the app run without API keys, scraping, network access, or a large local dataset. It includes Bay Area and remote postings for:

- Business Analyst.
- Data Analyst.
- Business Systems Analyst.
- Project Manager.
- Associate Project Manager.
- Technical Project Coordinator.

## Current Retrieval Method

`careercompass/rag.py` implements deterministic lexical retrieval:

1. Tokenize the target role and location.
2. Score postings by role/location/skill overlap.
3. Return the top postings with retrieval scores and evidence summaries.
4. Derive market skills by counting skills across retrieved postings.

This gives the Market Demand Agent retrieved evidence now and creates a clean replacement point for ChromaDB/vector search later.

## Next RAG Upgrade

Nhi can replace or extend `retrieve_job_postings()` and `careercompass/kaggle_linkedin.py` with:

- ChromaDB collection creation.
- Embeddings using OpenAI `text-embedding-3-small`.
- Metadata filters for role, location, company, and posting date.
- Top-k retrieval with source IDs and evidence snippets.

The output should keep the current shape:

```python
[
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
]
```

## Bias And Limitations

The local sample and even the Kaggle corpus are not guaranteed to represent the full labor market. The final report should acknowledge that:

- Bay Area tech companies are overrepresented.
- Entry-level postings can vary widely by company.
- Skill counts from small samples should be treated as directional, not authoritative.
- Recommendations should be reviewed with a career advisor.

