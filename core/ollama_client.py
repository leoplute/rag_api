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


# Asks the LLM to generate a list of questions that a given chunk of text answers.
# Params: chunk (str) - the source text, n (int) - how many questions to generate
# Returns: list of question strings (empty list if generation or parsing fails)
async def generate_hypothetical_questions(chunk: str, n: int = 3) -> list[str]:
    prompt = (
        f"Generate exactly {n} specific questions that the following text directly answers. "
        f"Return only a numbered list with no extra commentary.\n\n"
        f"Text:\n{chunk}\n\nQuestions:"
    )
    payload = {
        "model": CHAT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            response.raise_for_status()

        raw = response.json()["message"]["content"]

        # Parse numbered or bulleted lines, stripping leading markers
        questions = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            # Strip "1." / "1)" / "-" / "*" prefixes
            for prefix in ("1.", "2.", "3.", "4.", "5.", "1)", "2)", "3)", "4)", "5)", "-", "*"):
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()
                    break
            if line:
                questions.append(line)

        return questions[:n]

    except Exception:
        return []


# Asks the LLM whether two text passages directly contradict each other on a specific fact.
# Params: chunk_a (str) - first passage, chunk_b (str) - second passage
# Returns: True if the LLM says they contradict, False otherwise (including on failure)
async def check_contradiction(chunk_a: str, chunk_b: str) -> bool:
    prompt = (
        "Do these two passages directly contradict each other on a specific fact or claim? "
        "Answer only 'yes' or 'no'.\n\n"
        f"Passage A:\n{chunk_a}\n\n"
        f"Passage B:\n{chunk_b}"
    )
    payload = {
        "model": CHAT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            response.raise_for_status()
        answer = response.json()["message"]["content"].strip().lower()
        return answer.startswith("yes")
    except Exception:
        return False


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
