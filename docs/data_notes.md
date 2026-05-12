# CareerCompass Data Notes

This is the first RAG/Data lane implementation.

## Current Dataset

The MVP includes a small local job-posting sample:

```text
careercompass/data/job_postings.json
```

The sample is intentionally lightweight so the app can run without API keys, scraping, network access, or ChromaDB setup. It includes Bay Area and remote postings for:

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

Nhi can replace or extend `retrieve_job_postings()` with:

- Kaggle LinkedIn job posting dataset ingestion.
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

## Rubric-Ready RAG Story

For the final submission, describe the current RAG layer as a reliable local
retrieval baseline and the ChromaDB/Kaggle job-posting lane as the production
upgrade path.

- Current demo: lexical retrieval over local job postings with retrieval scores,
  metadata, and evidence summaries.
- Upgrade path: ingest a larger LinkedIn/Kaggle-style dataset, embed postings,
  store them in ChromaDB, and preserve the same returned posting contract.
- Reason for the staged design: the demo remains deterministic and API-key-free
  while still showing how retrieved labor-market evidence grounds the agents.

## Bias And Limitations

The current local sample is not representative of the full labor market. It is useful for demo reliability, but the final report should acknowledge that:

- Bay Area tech companies are overrepresented.
- Entry-level postings can vary widely by company.
- Skill counts from small samples should be treated as directional, not authoritative.
- Recommendations should be reviewed with a career advisor.

