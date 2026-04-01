
from fastapi import APIRouter, Query
from db.sqlite_client import get_connection

router = APIRouter()

@router.get("/")
def search_documents(
    q: str = Query(..., min_length=1),
    corpus: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100)
):
    conn = get_connection()
    offset = (page - 1) * limit

    try:
        if corpus:
            rows = conn.execute("""
                SELECT DISTINCT d.id, d.corpus, d.filename, d.page_count, f.page_num
                FROM documents_fts f
                JOIN documents d ON f.doc_id = d.id
                WHERE documents_fts MATCH ? AND d.corpus = ?
                LIMIT ? OFFSET ?
            """, (q, corpus, limit, offset)).fetchall()
        else:
            rows = conn.execute("""
                SELECT DISTINCT d.id, d.corpus, d.filename, d.page_count, f.page_num
                FROM documents_fts f
                JOIN documents d ON f.doc_id = d.id
                WHERE documents_fts MATCH ?
                LIMIT ? OFFSET ?
            """, (q, limit, offset)).fetchall()
    except Exception as e:
        return {"query": q, "results": [], "error": str(e), "page": page, "limit": limit}

    conn.close()

    return {
        "query": q,
        "results": [dict(r) for r in rows],
        "page": page,
        "limit": limit
    }