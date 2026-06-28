# RAG API

A local RAG (Retrieval-Augmented Generation) API built with FastAPI and ollama. Designed to be a reusable AI backend — embed program-specific data into named collections and get context-aware answers via a clean HTTP interface.

## Models

| Role | Model |
|------|-------|
| Chat | `llama3.2:3b` (via ollama) |
| Embeddings | `all-minilm:22m` (via ollama) |

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- [ollama](https://ollama.com/) running locally

## Setup

```bash
uv sync

ollama pull llama3.2:3b
ollama pull all-minilm:22m
```

## Running

```bash
# Start ollama first
ollama serve

# Start the API (hot reload enabled)
uv run main.py
```

API available at `http://localhost:8000`.

---

## How It Works

### Hypothetical Question Indexing

When you embed a document, the system does more than just chunk and store raw text. For each chunk, it uses the local LLM to generate 3 hypothetical questions that the chunk directly answers — then embeds and stores those questions as separate, searchable entries alongside the chunk.

At query time, your question matches against both raw chunk text *and* these hypothetical questions. When a question entry is the best match, the system dereferences it back to its parent chunk text before passing context to the LLM. This improves retrieval significantly for factual questions because you're matching question-to-question rather than question-to-prose.

Each embedded file produces 4× the number of ChromaDB entries (1 chunk + 3 questions per chunk), which is reflected in `chunk_count` from `GET /collections`.

### Retrieval Analytics

Every time a chat query retrieves context from a collection, the system records which source files were used. This data is stored in a local SQLite database (`analytics.db`) and exposed through `GET /collections/{name}/analytics`. Use it to see which documents are actively contributing to answers and which are "dead" — embedded but never retrieved.

### Confidence Scoring

Every `/chat` response with a collection includes a `confidence` score between 0 and 1. This reflects how closely the retrieved chunks matched your query (derived from ChromaDB's vector distances). A high score means the collection contained content very similar to your question; a low score is a signal that the answer may be speculative or the collection doesn't cover the topic well.

### Contradiction Detection

When you embed a new file, the system automatically scans its chunks against existing content in the same collection. If a new chunk is highly similar to a chunk from a different file, the LLM checks whether they contradict each other on a specific fact. Any contradictions are returned in the embed response so you can decide whether to remove conflicting data before it affects query quality.

### Context Expansion

When a chunk is retrieved, the system also fetches its neighboring chunks (the one immediately before and after it in the original document). This prevents relevant sentences at chunk boundaries from being cut off, giving the LLM a fuller window of context around each relevant passage.

### Multi-Collection Querying

A single `/chat` request can search across multiple named collections simultaneously. Results from all collections are merged and ranked by relevance before being passed to the LLM, so you get a unified answer grounded in data from multiple sources.

---

## Endpoints

### `POST /chat`

Chat with the local model. Optionally ground the response in one or more embedded collections.

**Request**
```json
{
  "message": "Who approved the Stratos project area?",
  "collection_name": "my_project"
}
```

For multiple collections:
```json
{
  "message": "Compare the two projects",
  "collection_names": ["project_a", "project_b"]
}
```

**Response**
```json
{
  "response": "The Military Installation Development Authority (MIDA)...",
  "model": "llama3.2:3b",
  "confidence": 0.812
}
```

`confidence` is `null` when no collection is used. A value above ~0.7 generally means the collection had relevant content; below ~0.4 suggests the answer may not be grounded in your data.

---

### `POST /embed`

Chunk, embed, and store a `.txt` file into a named collection. Also generates hypothetical questions per chunk and scans for contradictions against existing files. The collection is created automatically if it doesn't exist.

**Request** — `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `file` | file | `.txt` file to embed |
| `collection_name` | string | Collection to store chunks in |

**Response**
```json
{
  "collection_name": "my_project",
  "filename": "context.txt",
  "chunks_added": 31,
  "contradictions": [
    {
      "new_chunk_preview": "The project spans 40,000 acres...",
      "conflicting_file": "old_report.txt",
      "conflicting_chunk_preview": "The project area covers 35,000 acres..."
    }
  ]
}
```

> `chunks_added` reflects source chunks only — question entries are stored silently alongside them. `contradictions` is an empty list when no conflicts are found.

---

### `DELETE /embed`

Remove all embedded chunks (and their associated question entries) for a specific file from a collection. Returns 404 if the filename isn't found.

**Query params:** `collection_name`, `filename`

```
DELETE /embed?collection_name=my_project&filename=context.txt
```

**Response**
```json
{
  "collection_name": "my_project",
  "filename": "context.txt",
  "chunks_deleted": 124
}
```

---

### `GET /collections`

List all collections and their total entry counts (includes both chunk and question entries).

**Response**
```json
{
  "collections": [
    { "name": "my_project", "chunk_count": 352 },
    { "name": "other_project", "chunk_count": 180 }
  ]
}
```

---

### `GET /collections/{name}/files`

List the distinct source files embedded in a specific collection.

**Response**
```json
{
  "collection_name": "my_project",
  "files": ["context.txt", "docs.txt"]
}
```

---

### `GET /collections/{name}/analytics`

Return retrieval analytics for a collection. Shows how many times each source file's chunks have been surfaced in a chat query, and flags any files that have never been retrieved (dead files).

**Response**
```json
{
  "collection_name": "my_project",
  "file_stats": [
    { "filename": "context.txt", "retrieval_count": 47 },
    { "filename": "old_docs.txt", "retrieval_count": 0 }
  ],
  "dead_files": ["old_docs.txt"],
  "total_tracked_retrievals": 47
}
```

Dead files are a signal that a document either contains redundant information already covered by other files, or is phrased in a way that the embedding model doesn't match well against real queries. Consider removing and re-embedding with cleaner source text.

---

## Collections

Collections are the core multi-tenancy primitive. Each program using this API should have its own named collection, keeping its embedded data isolated from other programs.

```
POST /embed                        →  loads data into a collection
POST /chat                         →  queries a collection for context
DELETE /embed                      →  removes a specific file's data
GET /collections                   →  see all collections
GET /collections/{name}/files      →  see what's embedded in a collection
GET /collections/{name}/analytics  →  see retrieval usage and dead files
```

---

## Usage Example

```python
import requests

BASE = "http://localhost:8000"

# Embed a file into a collection
with open("my_docs.txt", "rb") as f:
    r = requests.post(
        f"{BASE}/embed",
        files={"file": ("my_docs.txt", f, "text/plain")},
        data={"collection_name": "my_project"},
    )
result = r.json()
print(f"Embedded {result['chunks_added']} chunks")
if result["contradictions"]:
    print("Contradictions found:", result["contradictions"])

# Chat grounded in a single collection
r = requests.post(f"{BASE}/chat", json={
    "message": "What is the main topic covered?",
    "collection_name": "my_project",
})
data = r.json()
print(data["response"])
print(f"Confidence: {data['confidence']}")  # e.g. 0.82

# Chat grounded in multiple collections at once
r = requests.post(f"{BASE}/chat", json={
    "message": "Compare the approaches in both documents",
    "collection_names": ["project_a", "project_b"],
})
print(r.json()["response"])

# See which files are contributing to answers
r = requests.get(f"{BASE}/collections/my_project/analytics")
analytics = r.json()
print("Dead files:", analytics["dead_files"])
for stat in analytics["file_stats"]:
    print(f"  {stat['filename']}: {stat['retrieval_count']} retrievals")

# Remove a specific file from a collection
r = requests.delete(f"{BASE}/embed", params={
    "collection_name": "my_project",
    "filename": "my_docs.txt",
})
print(f"Deleted {r.json()['chunks_deleted']} entries")
```

---

## Project Structure

```
RAG_API/
├── main.py               # Entry point, starts uvicorn
├── api/
│   └── routes.py         # All API endpoints
├── core/
│   ├── embedding.py      # Chunking, question generation, contradiction detection, and retrieval
│   ├── vector_store.py   # ChromaDB operations
│   ├── ollama_client.py  # ollama communication layer
│   └── analytics.py      # SQLite-based retrieval analytics
└── pyproject.toml
```
