# Manages the persistent ChromaDB client and all collection operations.
# Each collection represents one program's embedded data set.

import chromadb

CHROMA_PATH = "./chroma_db"

_client = chromadb.PersistentClient(path=CHROMA_PATH)


# Fetches an existing collection or creates it if it doesn't exist.
# Params: collection_name (str) - the name of the collection to get or create
# Returns: a ChromaDB Collection object
def get_or_create_collection(collection_name: str):
    return _client.get_or_create_collection(name=collection_name)


# Adds a set of text chunks and their embeddings to a named collection.
# Params: collection_name (str), chunks (list of text strings),
#         embeddings (list of float vectors), ids (list of unique string IDs),
#         metadatas (list of dicts) - optional per-chunk metadata (e.g. source filename)
# Returns: None
def add_chunks(
    collection_name: str,
    chunks: list[str],
    embeddings: list[list[float]],
    ids: list[str],
    metadatas: list[dict] | None = None,
) -> None:
    collection = get_or_create_collection(collection_name)
    collection.add(documents=chunks, embeddings=embeddings, ids=ids, metadatas=metadatas)


# Returns a list of all collection names and their total chunk counts.
# Returns: list of dicts with "name" and "chunk_count" keys
def list_collections() -> list[dict]:
    collections = _client.list_collections()
    return [
        {"name": col.name, "chunk_count": col.count()}
        for col in collections
    ]


# Returns the distinct source filenames embedded in a given collection.
# Params: collection_name (str)
# Returns: list of unique filename strings
def list_collection_files(collection_name: str) -> list[str]:
    collection = get_or_create_collection(collection_name)
    results = collection.get(include=["metadatas"])

    # Pull unique source values, skipping chunks that have no source metadata
    seen = set()
    for meta in results["metadatas"]:
        if meta and "source" in meta:
            seen.add(meta["source"])

    return sorted(seen)


# Deletes all chunks belonging to a specific source file from a collection.
# Params: collection_name (str), filename (str) - the original filename used when embedding
# Returns: number of chunks deleted
def delete_file_chunks(collection_name: str, filename: str) -> int:
    collection = get_or_create_collection(collection_name)

    # Fetch all chunk IDs that were stored with this source filename
    results = collection.get(where={"source": filename})
    ids_to_delete = results["ids"]

    if not ids_to_delete:
        return 0

    collection.delete(ids=ids_to_delete)
    return len(ids_to_delete)


# Queries a collection for the most semantically similar chunks to a given embedding.
# Params: collection_name (str), query_embedding (list of floats),
#         n_results (int) - number of top chunks to return
# Returns: list of matching text chunk strings
def query_collection(
    collection_name: str,
    query_embedding: list[float],
    n_results: int = 10,
) -> list[str]:
    collection = get_or_create_collection(collection_name)
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    return results["documents"][0]
