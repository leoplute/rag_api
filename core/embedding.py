# Handles text chunking and the full document embedding pipeline.
# Chunks a document, gets embeddings for each chunk via ollama, and stores them in ChromaDB.

from core.ollama_client import get_embedding
from core.vector_store import add_chunks, delete_file_chunks, query_collection

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


# Splits a text string into overlapping fixed-size chunks.
# Params: text (str) - the full document text to split
# Returns: list of text chunk strings
def chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0

    while start < len(text):
        chunks.append(text[start : start + CHUNK_SIZE])
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


# Full pipeline: chunks a document, embeds each chunk, and stores in the named collection.
# Params: text (str) - document content, filename (str) - used to build unique chunk IDs,
#         collection_name (str) - the ChromaDB collection to store into
# Returns: the number of chunks embedded
async def embed_document(text: str, filename: str, collection_name: str) -> int:
    chunks = chunk_text(text)

    # Embed each chunk sequentially (ollama is local, no parallelism benefit)
    embeddings = [await get_embedding(chunk) for chunk in chunks]

    ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": filename} for _ in chunks]
    add_chunks(collection_name, chunks, embeddings, ids, metadatas)

    return len(chunks)


# Embeds a query string and retrieves the most relevant chunks from a collection.
# Params: query (str) - the user's question, collection_name (str),
#         n_results (int) - how many chunks to return
# Returns: list of relevant text chunk strings
async def retrieve_context(
    query: str, collection_name: str, n_results: int = 10
) -> list[str]:
    query_embedding = await get_embedding(query)
    return query_collection(collection_name, query_embedding, n_results)
