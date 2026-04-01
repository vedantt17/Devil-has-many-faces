from fastapi import APIRouter, Query, HTTPException
from db.sqlite_client import get_connection
from db.mongo_client import get_db

router = APIRouter()

@router.get("/")
def list_documents(
    corpus: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100)
):
    conn = get_connection()
    offset = (page - 1) * limit

    if corpus:
        rows = conn.execute("""
            SELECT id, corpus, filename, page_count, is_scanned, created_at
            FROM documents WHERE corpus = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (corpus, limit, offset)).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) FROM documents WHERE corpus = ?", (corpus,)
        ).fetchone()[0]
    else:
        rows = conn.execute("""
            SELECT id, corpus, filename, page_count, is_scanned, created_at
            FROM documents
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

    conn.close()
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "documents": [dict(r) for r in rows]
    }

@router.get("/{doc_id}")
def get_document(doc_id: str):
    conn = get_connection()
    doc = conn.execute(
        "SELECT * FROM documents WHERE id = ?", (doc_id,)
    ).fetchone()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    entities = conn.execute("""
        SELECT e.name, e.type, COUNT(m.id) as mentions
        FROM mentions m
        JOIN entities e ON m.entity_id = e.id
        WHERE m.doc_id = ?
        GROUP BY e.name, e.type
        ORDER BY mentions DESC
        LIMIT 20
    """, (doc_id,)).fetchall()

    redactions = conn.execute("""
        SELECT page_num, redaction_count, estimated_chars
        FROM redactions WHERE doc_id = ?
        ORDER BY page_num
    """, (doc_id,)).fetchall()

    conn.close()

    db = get_db()
    mongo_doc = db.raw_docs.find_one({"doc_id": doc_id}, {"_id": 0, "pages": 1})
    pages = mongo_doc.get("pages", []) if mongo_doc else []

    return {
        "document": dict(doc),
        "entities": [dict(e) for e in entities],
        "redactions": [dict(r) for r in redactions],
        "pages": pages
    }