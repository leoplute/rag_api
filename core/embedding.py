# Handles text chunking and the full document embedding pipeline.
# Chunks a document, generates hypothetical questions per chunk for better retrieval,
# stores everything in ChromaDB, detects contradictions against existing content,
# and retrieves context with confidence scoring, context expansion, and multi-collection support.

from core.analytics import record_retrieval
from core.ollama_client import check_contradiction, generate_hypothetical_questions, get_embedding
from core.vector_store import add_chunks, get_documents_by_ids, query_collection_raw

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Distance threshold for triggering contradiction LLM checks.
# Chunks from different files with distance below this are similar enough to potentially conflict.
CONTRADICTION_DISTANCE_THRESHOLD = 0.5
# Max chunks per embed to scan for contradictions (controls how many extra LLM calls can occur).
CONTRADICTION_CHECK_LIMIT = 20


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


# Parses a chunk ID of the form "{filename}_chunk_{i}" into its filename and index.
# Params: chunk_id (str)
# Returns: (filename, index) tuple, or None if the ID doesn't match the expected format
def _parse_chunk_id(chunk_id: str) -> tuple[str, int] | None:
    parts = chunk_id.rsplit("_chunk_", 1)
    if len(parts) != 2:
        return None
    try:
        return parts[0], int(parts[1])
    except ValueError:
        return None


# Full pipeline: chunks a document, embeds each chunk, generates and embeds hypothetical
# questions per chunk, then scans for contradictions against existing collection content.
# Params: text (str) - document content, filename (str) - used to build unique chunk IDs,
#         collection_name (str) - the ChromaDB collection to store into
# Returns: dict with "chunks_added" (int) and "contradictions" (list of dicts)
async def embed_document(text: str, filename: str, collection_name: str) -> dict:
    chunks = chunk_text(text)

    # Embed each chunk and store in ChromaDB
    chunk_embeddings = [await get_embedding(chunk) for chunk in chunks]
    chunk_ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]
    chunk_metadatas = [{"source": filename, "type": "chunk"} for _ in chunks]
    add_chunks(collection_name, chunks, chunk_embeddings, chunk_ids, chunk_metadatas)

    # Generate hypothetical questions for each chunk and embed them separately.
    # These act as additional retrieval anchors — a query matches against questions
    # that the chunk answers, not just the raw chunk text.
    question_texts, question_embeddings, question_ids, question_metadatas = [], [], [], []

    for i, (chunk, chunk_id) in enumerate(zip(chunks, chunk_ids)):
        questions = await generate_hypothetical_questions(chunk, n=3)
        for j, question in enumerate(questions):
            q_embedding = await get_embedding(question)
            question_texts.append(question)
            question_embeddings.append(q_embedding)
            question_ids.append(f"{chunk_id}_q{j}")
            question_metadatas.append({
                "source": filename,
                "type": "question",
                "parent_id": chunk_id,
            })

    if question_texts:
        add_chunks(collection_name, question_texts, question_embeddings, question_ids, question_metadatas)

    # Scan new chunks against existing collection content for contradictions.
    # Reuses pre-computed embeddings to avoid re-embedding.
    contradictions = await detect_contradictions(chunks, chunk_embeddings, filename, collection_name)

    return {"chunks_added": len(chunks), "contradictions": contradictions}


# Scans newly embedded chunks against other files already in the collection for contradictions.
# Uses pre-computed embeddings to find similar chunks from other files, then asks the LLM
# if they actually contradict on a specific fact. LLM is only called when distance is low enough.
# Params: chunks (list[str]), chunk_embeddings (list of float vectors) - must be same length,
#         filename (str) - the file just embedded (excluded from comparison),
#         collection_name (str)
# Returns: list of contradiction dicts with preview text from both sides
async def detect_contradictions(
    chunks: list[str],
    chunk_embeddings: list[list[float]],
    filename: str,
    collection_name: str,
) -> list[dict]:
    contradictions = []

    for chunk, embedding in zip(chunks[:CONTRADICTION_CHECK_LIMIT], chunk_embeddings[:CONTRADICTION_CHECK_LIMIT]):
        raw = query_collection_raw(
            collection_name,
            embedding,
            n_results=3,
            where={"type": "chunk"},
        )
        if not raw["ids"]:
            continue

        # Check the closest chunk from a different source file
        for doc_id, doc, meta, dist in zip(
            raw["ids"], raw["documents"], raw["metadatas"], raw["distances"]
        ):
            source = (meta or {}).get("source", "")
            if source == filename:
                continue
            if dist > CONTRADICTION_DISTANCE_THRESHOLD:
                break
            is_contradiction = await check_contradiction(chunk, doc)
            if is_contradiction:
                contradictions.append({
                    "new_chunk_preview": chunk[:150],
                    "conflicting_file": source,
                    "conflicting_chunk_preview": doc[:150],
                })
            break

    return contradictions


# Embeds a query string, retrieves the most relevant chunks from one or more collections,
# dereferences any question-type hits back to their parent chunks, expands context with
# neighboring chunks, and computes a confidence score based on retrieval distances.
# Params: query (str) - the user's question,
#         collection_names (list[str]) - one or more ChromaDB collections to search,
#         n_results (int) - how many unique chunks to return
# Returns: dict with "chunks" (list[str]) and "confidence" (float 0.0-1.0)
async def retrieve_context(
    query: str,
    collection_names: list[str],
    n_results: int = 15,
) -> dict:
    query_embedding = await get_embedding(query)

    # Query each collection and merge all candidates sorted by distance (closest first)
    all_raw: list[tuple[float, str, str, dict, str]] = []

    for col_name in collection_names:
        raw = query_collection_raw(col_name, query_embedding, n_results)
        for dist, doc_id, doc, meta in zip(
            raw["distances"], raw["ids"], raw["documents"], raw["metadatas"]
        ):
            all_raw.append((dist, doc_id, doc, meta, col_name))

    if not all_raw:
        return {"chunks": [], "confidence": 0.0}

    all_raw.sort(key=lambda x: x[0])

    # Batch-fetch all parent chunks needed for question dereference, grouped by collection
    question_parent_ids_by_col: dict[str, set[str]] = {}
    for dist, doc_id, doc, meta, col in all_raw:
        if (meta or {}).get("type") == "question":
            parent_id = (meta or {}).get("parent_id")
            if parent_id:
                question_parent_ids_by_col.setdefault(col, set()).add(parent_id)

    parent_texts_by_col: dict[str, dict[str, str]] = {}
    for col, parent_ids in question_parent_ids_by_col.items():
        parent_texts_by_col[col] = get_documents_by_ids(col, list(parent_ids))

    # Walk ranked results in order, resolving questions to their parent chunk inline.
    # Stop once we have enough unique chunks.
    result_chunks: list[dict] = []
    seen_chunk_ids: set[str] = set()

    for dist, doc_id, doc, meta, col in all_raw:
        entry_type = (meta or {}).get("type", "chunk")
        source = (meta or {}).get("source", "")

        if entry_type == "question":
            parent_id = (meta or {}).get("parent_id")
            col_parents = parent_texts_by_col.get(col, {})
            if parent_id and parent_id not in seen_chunk_ids and parent_id in col_parents:
                seen_chunk_ids.add(parent_id)
                result_chunks.append({
                    "id": parent_id,
                    "text": col_parents[parent_id],
                    "source": source,
                    "collection": col,
                    "distance": dist,
                })
        else:
            if doc_id not in seen_chunk_ids:
                seen_chunk_ids.add(doc_id)
                result_chunks.append({
                    "id": doc_id,
                    "text": doc,
                    "source": source,
                    "collection": col,
                    "distance": dist,
                })

        if len(result_chunks) >= n_results:
            break

    # Context expansion: fetch the chunk immediately before and after each retrieved chunk.
    # Groups neighbor IDs by collection to batch the lookups efficiently.
    # Uses expansion_seen to deduplicate — two adjacent retrieved chunks can share the same neighbor.
    expansion_ids_by_col: dict[str, list[str]] = {}
    expansion_seen: set[str] = set()
    for chunk in result_chunks:
        parsed = _parse_chunk_id(chunk["id"])
        if not parsed:
            continue
        fname, idx = parsed
        col = chunk["collection"]
        neighbor_ids = expansion_ids_by_col.setdefault(col, [])
        if idx > 0:
            prev_id = f"{fname}_chunk_{idx - 1}"
            if prev_id not in seen_chunk_ids and prev_id not in expansion_seen:
                neighbor_ids.append(prev_id)
                expansion_seen.add(prev_id)
        next_id = f"{fname}_chunk_{idx + 1}"
        if next_id not in seen_chunk_ids and next_id not in expansion_seen:
            neighbor_ids.append(next_id)
            expansion_seen.add(next_id)

    for col, expand_ids in expansion_ids_by_col.items():
        if not expand_ids:
            continue
        neighbor_texts = get_documents_by_ids(col, expand_ids)
        for nid, ntext in neighbor_texts.items():
            if nid not in seen_chunk_ids:
                seen_chunk_ids.add(nid)
                result_chunks.append({
                    "id": nid,
                    "text": ntext,
                    "source": nid.rsplit("_chunk_", 1)[0],
                    "collection": col,
                    "distance": None,
                })

    # Confidence is computed from the top-5 directly retrieved chunks (not expanded neighbors).
    # Uses only the best matches to avoid diluting the signal with lower-ranked results.
    # Divides by 1.5 to account for all-minilm L2 distances typically ranging 0-1.5 for real content.
    direct_distances = [r["distance"] for r in result_chunks if r["distance"] is not None]
    if direct_distances:
        top_distances = direct_distances[:5]
        avg_dist = sum(top_distances) / len(top_distances)
        confidence = round(max(0.0, min(1.0, 1.0 - avg_dist / 1.5)), 3)
    else:
        confidence = 0.0

    # Record analytics for directly retrieved chunks only, grouped by collection
    direct_chunks = [r for r in result_chunks if r["distance"] is not None]
    if direct_chunks:
        for col in set(r["collection"] for r in direct_chunks):
            col_chunks = [r for r in direct_chunks if r["collection"] == col]
            record_retrieval(col, [r["id"] for r in col_chunks], [r["source"] for r in col_chunks])

    return {"chunks": [r["text"] for r in result_chunks], "confidence": confidence}
