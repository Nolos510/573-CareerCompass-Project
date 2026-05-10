import pandas as pd
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI

# ── 1. Load data ──────────────────────────────────────────────────────────────
df = pd.read_csv("DATA/postings.csv").head(5000)
print(f"Loaded {len(df)} job postings")

# ── 2. Prepare documents ──────────────────────────────────────────────────────
# Combine relevant columns into one text block per job
def make_document(row):
    parts = []
    for col in ["title", "description", "skills", "qualifications", "company_name", "location"]:
        if col in df.columns and pd.notna(row.get(col)):
            parts.append(str(row[col]))
    return " | ".join(parts)

df["document"] = df.apply(make_document, axis=1)
documents = df["document"].tolist()
print(f"Prepared {len(documents)} documents")

# ── 3. Split long texts ───────────────────────────────────────────────────────
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.create_documents(documents)
print(f"Split into {len(chunks)} chunks")

# ── 4. Store in ChromaDB ──────────────────────────────────────────────────────
client = chromadb.PersistentClient(path="DATA/chroma_db")
collection = client.get_or_create_collection("job_postings")

batch_size = 5000
all_docs = [c.page_content for c in chunks]
all_ids = [f"doc_{i}" for i in range(len(chunks))]

for i in range(0, len(all_docs), batch_size):
    batch_docs = all_docs[i:i+batch_size]
    batch_ids = all_ids[i:i+batch_size]
    collection.add(documents=batch_docs, ids=batch_ids)
    print(f"Stored batch {i//batch_size + 1} / {len(all_docs)//batch_size + 1}")

print(f"Stored {len(chunks)} chunks in ChromaDB")

# ── 5. Test a query ───────────────────────────────────────────────────────────
results = collection.query(query_texts=["data engineer python"], n_results=3)
print("\n--- Sample Query Results ---")
for doc in results["documents"][0]:
    print(doc[:200])
    print("---")
    