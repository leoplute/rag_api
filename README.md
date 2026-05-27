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

## Endpoints

### `POST /chat`

Chat with the local model. Optionally ground the response in an embedded collection by passing `collection_name`.

**Request**
```json
{
  "message": "Who approved the Stratos project area?",
  "collection_name": "my_project"
}
```

**Response**
```json
{
  "response": "The Military Installation Development Authority (MIDA)...",
  "model": "llama3.2:3b"
}
```

---

### `POST /embed`

Chunk, embed, and store a `.txt` file into a named collection. The collection is created automatically if it doesn't exist.

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
  "chunks_added": 31
}
```

---

### `DELETE /embed`

Remove all embedded chunks for a specific file from a collection. Returns 404 if the filename isn't found.

**Query params:** `collection_name`, `filename`

```
DELETE /embed?collection_name=my_project&filename=context.txt
```

**Response**
```json
{
  "collection_name": "my_project",
  "filename": "context.txt",
  "chunks_deleted": 31
}
```

---

### `GET /collections`

List all collections and their total chunk counts.

**Response**
```json
{
  "collections": [
    { "name": "my_project", "chunk_count": 88 },
    { "name": "other_project", "chunk_count": 45 }
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

## Collections

Collections are the core multi-tenancy primitive. Each program using this API should have its own named collection, keeping its embedded data isolated from other programs.

```
POST /embed          →  loads data into a collection
POST /chat           →  queries a collection for context
DELETE /embed        →  removes a specific file's data
GET /collections     →  see all collections
GET /collections/{name}/files  →  see what's embedded in a collection
```

## Project Structure

```
RAG_API/
├── main.py               # Entry point, starts uvicorn
├── api/
│   └── routes.py         # All API endpoints
├── core/
│   ├── embedding.py      # Chunking and embed pipeline
│   ├── vector_store.py   # ChromaDB operations
│   └── ollama_client.py  # ollama communication layer
└── pyproject.toml
```
