# Handles all communication with the locally running ollama server.
# Provides async functions for sending chat messages and receiving responses.

import httpx

OLLAMA_BASE_URL = "http://localhost:11434"
CHAT_MODEL = "llama3.2:3b"
EMBEDDING_MODEL = "all-minilm:22m"


# Sends a single user message to the ollama chat API and returns the assistant response text.
# Params: message (str) - the user's message
# Returns: the assistant's response as a plain string
async def send_chat_message(message: str) -> str:
    payload = {
        "model": CHAT_MODEL,
        "messages": [{"role": "user", "content": message}],
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
        )
        response.raise_for_status()

    return response.json()["message"]["content"]


# Sends a text string to the ollama embeddings API and returns its vector representation.
# Params: text (str) - the text to embed
# Returns: a list of floats representing the embedding vector
async def get_embedding(text: str) -> list[float]:
    payload = {"model": EMBEDDING_MODEL, "prompt": text}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json=payload,
        )
        response.raise_for_status()

    return response.json()["embedding"]
