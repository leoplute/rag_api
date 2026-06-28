# Tracks chunk retrieval history in a local SQLite database for usage analytics.
# Used to surface retrieval frequency per file and detect dead (never-retrieved) documents.

import sqlite3
from datetime import datetime

ANALYTICS_DB_PATH = "./analytics.db"


# Opens a connection and ensures the retrievals table exists.
def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(ANALYTICS_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS retrievals (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_name TEXT NOT NULL,
            chunk_id      TEXT NOT NULL,
            source_file   TEXT NOT NULL,
            retrieved_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


# Records that a set of chunks were surfaced during a retrieval query.
# Params: collection_name (str), chunk_ids (list of str), source_files (list of str)
#         - chunk_ids and source_files must be the same length and positionally aligned
# Returns: None
def record_retrieval(
    collection_name: str,
    chunk_ids: list[str],
    source_files: list[str],
) -> None:
    now = datetime.utcnow().isoformat()
    conn = _get_connection()
    conn.executemany(
        "INSERT INTO retrievals (collection_name, chunk_id, source_file, retrieved_at) VALUES (?, ?, ?, ?)",
        [(collection_name, cid, src, now) for cid, src in zip(chunk_ids, source_files)],
    )
    conn.commit()
    conn.close()


# Returns analytics for a collection: per-file retrieval counts and dead files.
# Params: collection_name (str),
#         embedded_files (list[str]) - currently embedded filenames from ChromaDB
# Returns: dict with file_stats, dead_files, and total_tracked_retrievals
def get_collection_analytics(collection_name: str, embedded_files: list[str]) -> dict:
    conn = _get_connection()

    rows = conn.execute(
        "SELECT source_file, COUNT(*) FROM retrievals WHERE collection_name = ? GROUP BY source_file",
        (collection_name,),
    ).fetchall()
    conn.close()

    # Build a lookup of retrieval counts per file
    retrieval_counts = {row[0]: row[1] for row in rows}

    file_stats = [
        {"filename": f, "retrieval_count": retrieval_counts.get(f, 0)}
        for f in embedded_files
    ]

    dead_files = [s["filename"] for s in file_stats if s["retrieval_count"] == 0]

    return {
        "collection_name": collection_name,
        "file_stats": file_stats,
        "dead_files": dead_files,
        "total_tracked_retrievals": sum(retrieval_counts.values()),
    }
