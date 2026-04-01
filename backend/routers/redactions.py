# Written by V
from fastapi import APIRouter, Query
from db.sqlite_client import get_connection

router = APIRouter()

@router.get("/")
def get_redaction_stats(corpus: str = Query(None)):
    conn = get_connection()

    total = conn.execute("""
        SELECT SUM(r.redaction_count) as total_redactions,
               SUM(r.estimated_chars) as total_chars
        FROM redactions r
        JOIN documents d ON r.doc_id = d.id
    """).fetchone()

    by_corpus = conn.execute("""
        SELECT d.corpus,
               COUNT(DISTINCT d.id) as docs_with_redactions,
               SUM(r.redaction_count) as total_redactions
        FROM redactions r
        JOIN documents d ON r.doc_id = d.id
        GROUP BY d.corpus
    """).fetchall()

    most_redacted = conn.execute("""
        SELECT d.filename, d.corpus,
               SUM(r.redaction_count) as total_redactions
        FROM redactions r
        JOIN documents d ON r.doc_id = d.id
        GROUP BY d.id
        ORDER BY total_redactions DESC
        LIMIT 10
    """).fetchall()

    conn.close()

    return {
        "total_redactions": total["total_redactions"] or 0,
        "total_chars_redacted": total["total_chars"] or 0,
        "by_corpus": [dict(r) for r in by_corpus],
        "most_redacted_docs": [dict(r) for r in most_redacted]
    }