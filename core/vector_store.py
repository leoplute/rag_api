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
#         embeddings (list of float vectors), ids (list of unique string IDs)
# Returns: None
def add_chunks(
    collection_name: str,
    chunks: list[str],
    embeddings: list[list[float]],
    ids: list[str],
) -> None:
    collection = get_or_create_collection(collection_name)
    collection.add(documents=chunks, embeddings=embeddings, ids=ids)


# Queries a collection for the most semantically similar chunks to a given embedding.
# Params: collection_name (str), query_embedding (list of floats),
#         n_results (int) - number of top chunks to return
# Returns: list of matching text chunk strings
def query_collection(
    collection_name: str,
    query_embedding: list[float],
    n_results: int = 5,
) -> list[str]:
    collection = get_or_create_collection(collection_name)
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    return results["documents"][0]
