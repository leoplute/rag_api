# Defines all API endpoints for the RAG API.
# Currently exposes a basic chat endpoint that forwards messages to the local ollama model.

from fastapi import APIRouter, Form, HTTPException, UploadFile
from pydantic import BaseModel

from core.embedding import embed_document, retrieve_context
from core.ollama_client import send_chat_message

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    collection_name: str | None = None


class ChatResponse(BaseModel):
    response: str
    model: str


# Accepts a user message and returns a response from the local llama3.2:3b model.
# Params: body (ChatRequest) - contains the user's message string
# Returns: ChatResponse with the assistant's reply and the model name used
@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    message = body.message

    if body.collection_name:
        try:
            chunks = await retrieve_context(body.message, body.collection_name)
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Retrieval error: {str(e)}")

        context = "\n\n".join(chunks)
        message = (
            f"Use the following context to answer the question. "
            f"If the context doesn't contain relevant information, answer from your general knowledge.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {body.message}"
        )

    try:
        reply = await send_chat_message(message)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama error: {str(e)}")

    return ChatResponse(response=reply, model="llama3.2:3b")


class EmbedResponse(BaseModel):
    collection_name: str
    filename: str
    chunks_added: int


# Accepts a .txt file and a collection name, chunks and embeds the content into ChromaDB.
# Params: file (UploadFile) - the text file to embed,
#         collection_name (str) - the ChromaDB collection to store chunks in
# Returns: EmbedResponse with the collection name, filename, and number of chunks added
@router.post("/embed", response_model=EmbedResponse)
async def embed_file(file: UploadFile, collection_name: str = Form(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")

    text = (await file.read()).decode("utf-8")

    try:
        chunks_added = await embed_document(text, file.filename, collection_name)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Embedding error: {str(e)}")

    return EmbedResponse(
        collection_name=collection_name,
        filename=file.filename,
        chunks_added=chunks_added,
    )
