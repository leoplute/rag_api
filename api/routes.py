# Defines all API endpoints for the RAG API.
# Currently exposes a basic chat endpoint that forwards messages to the local ollama model.

from fastapi import APIRouter, Form, HTTPException, UploadFile
from pydantic import BaseModel

from core.embedding import embed_document, retrieve_context
from core.vector_store import delete_file_chunks, list_collection_files, list_collections
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
            f"Answer the question using the provided context. "
            f"The context is authoritative and up-to-date — trust it over your training data, "
            f"even if it conflicts with what you already know. "
            f"If the context contains no relevant information, say so briefly.\n\n"
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


class DeleteEmbedResponse(BaseModel):
    collection_name: str
    filename: str
    chunks_deleted: int


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


# Removes all embedded chunks for a specific file from a named collection.
# Params: collection_name (str) - the ChromaDB collection to target,
#         filename (str) - the exact filename used when the file was originally embedded
# Returns: DeleteEmbedResponse with collection name, filename, and number of chunks removed
@router.delete("/embed", response_model=DeleteEmbedResponse)
async def delete_embedded_file(collection_name: str, filename: str):
    try:
        chunks_deleted = delete_file_chunks(collection_name, filename)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Delete error: {str(e)}")

    if chunks_deleted == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No chunks found for '{filename}' in collection '{collection_name}'",
        )

    return DeleteEmbedResponse(
        collection_name=collection_name,
        filename=filename,
        chunks_deleted=chunks_deleted,
    )


class CollectionSummary(BaseModel):
    name: str
    chunk_count: int


class CollectionListResponse(BaseModel):
    collections: list[CollectionSummary]


# Returns all ChromaDB collections and the number of chunks stored in each.
# Returns: CollectionListResponse containing a list of collection names and chunk counts
@router.get("/collections", response_model=CollectionListResponse)
async def get_collections():
    try:
        results = list_collections()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ChromaDB error: {str(e)}")

    return CollectionListResponse(
        collections=[CollectionSummary(**c) for c in results]
    )


class CollectionFilesResponse(BaseModel):
    collection_name: str
    files: list[str]


# Returns the distinct source filenames embedded in a specific collection.
# Params: name (str) - the collection name from the URL path
# Returns: CollectionFilesResponse with the collection name and list of filenames
@router.get("/collections/{name}/files", response_model=CollectionFilesResponse)
async def get_collection_files(name: str):
    try:
        files = list_collection_files(name)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ChromaDB error: {str(e)}")

    return CollectionFilesResponse(collection_name=name, files=files)
