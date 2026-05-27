## Ollama Rules

# Server Management Guardrails
NEVER start the Ollama server: Do not invoke `ollama serve`, attempt to initialize background service processes, or trigger launchctl/systemd commands. The user always starts the server manually before beginning development.

Connection Assumption: Assume the Ollama daemon is already active and exposed at the default endpoint (`http://localhost:11434`).

Connection Failures: If an API request to localhost fails with a connection error, report the failure immediately to the user. Do not try to self-heal, re-run scripts, or spin up the server.

# Model & Interaction Protocol
Interactive Approvals Only: If you think a model needs to be pulled (`ollama pull`), created from a Modelfile, or tested interactively via the CLI, you must suggest it in chat. NEVER execute these mutations autonomously.

Context Window Adjustments: Before writing or changing code that interfaces with Ollama APIs, verify the expected context limits or parameter shifts across model tiers (e.g., 1B, 3B, 8B parameters). Do not hardcode hidden parameter assumptions without proposing them.

# Python Environment & Dependency Control
Package Management: Always use `uv` for environment management, dependency execution, and running scripts (e.g., `uv run script.py` or `uv pip install`). Never fall back to naked `pip` or standard virtual environment creators unless requested.

ChromaDB / Vector Database Alignment: When modifying RAG components or orchestrating embedding generation, explicitly ensure the dimensions of the embedding model (e.g., `nomic-embed-text`, `all-minilm`) strictly match the collection layout in ChromaDB.

# Local RAG Architecture Constraints
No External Fallbacks: When debugging connection errors, token limitations, or context stuffing issues, do not switch or suggest switching to external proprietary APIs (like OpenAI or Anthropic endpoints) unless explicitly directed. The system must remain entirely local.

Streaming Responses: By default, structure API interactions with the local layer to support streaming (`stream=True`) where applicable to keep user interface feedback responsive.