# Written by V
from fastapi import APIRouter, Query
from db.sqlite_client import get_connection

router = APIRouter()

@router.get("/")
def get_timeline(
    corpus: str = Query(None),
    entity: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=200)
):
    conn = get_connection()
    offset = (page - 1) * limit

    query = """
        SELECT m.context, m.page_num, d.filename, d.corpus,
               e.name as entity_name, e.type as entity_type
        FROM mentions m
        JOIN documents d ON m.doc_id = d.id
        JOIN entities e ON m.entity_id = e.id
        WHERE e.type = 'DATE'
    """
    params = []

    if corpus:
        query += " AND d.corpus = ?"
        params.append(corpus)
    if entity:
        query += " AND e.name LIKE ?"
        params.append(f"%{entity}%")

    query += " ORDER BY d.corpus, d.filename LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return {"events": [dict(r) for r in rows], "page": page, "limit": limit}