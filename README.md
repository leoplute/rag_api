# RAG API

A local RAG (Retrieval-Augmented Generation) API built with FastAPI and ollama. Designed to be a reusable AI backend — embed program-specific data and get context-aware answers via a clean HTTP interface.

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
# Install dependencies
uv sync

# Pull required models
ollama pull llama3.2:3b
ollama pull all-minilm:22m
```

## Running

```bash
# Start ollama (if not already running)
ollama serve

# Start the API (hot reload enabled)
uv run main.py
```

API will be available at `http://localhost:8000`.

## Endpoints

### `POST /chat`

Send a message to the llama3.2:3b model and receive a response.

**Request**
```json
{
  "message": "What is retrieval-augmented generation?"
}
```

**Response**
```json
{
  "response": "RAG is a technique that...",
  "model": "llama3.2:3b"
}
```

## Project Structure

```
RAG_API/
├── main.py          # Entry point, starts uvicorn
├── api/
│   └── routes.py    # All API endpoints
├── core/
│   └── ollama_client.py  # ollama communication layer
└── pyproject.toml
```
