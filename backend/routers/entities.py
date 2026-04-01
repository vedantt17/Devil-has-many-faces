from fastapi import APIRouter, Query, HTTPException
from db.sqlite_client import get_connection

router = APIRouter()

@router.get("/")
def list_entities(
    type: str = Query(None),
    q: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100)
):
    conn = get_connection()
    offset = (page - 1) * limit

    query = "SELECT e.id, e.name, e.type, COUNT(m.id) as mention_count FROM entities e JOIN mentions m ON e.id = m.entity_id"
    params = []
    conditions = []

    if type:
        conditions.append("e.type = ?")
        params.append(type)
    if q:
        conditions.append("e.name LIKE ?")
        params.append(f"%{q}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " GROUP BY e.id ORDER BY mention_count DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return {"entities": [dict(r) for r in rows], "page": page, "limit": limit}

@router.get("/{name}")
def get_entity(name: str):
    conn = get_connection()

    entity = conn.execute(
        "SELECT * FROM entities WHERE name = ?", (name,)
    ).fetchone()

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    appearances = conn.execute("""
        SELECT d.filename, d.corpus, m.page_num, m.context
        FROM mentions m
        JOIN documents d ON m.doc_id = d.id
        WHERE m.entity_id = ?
        ORDER BY d.corpus, d.filename
        LIMIT 50
    """, (entity["id"],)).fetchall()

    cooccurrences = conn.execute("""
        SELECT e2.name, e2.type, COUNT(*) as shared_docs
        FROM mentions m1
        JOIN mentions m2 ON m1.doc_id = m2.doc_id
        JOIN entities e2 ON m2.entity_id = e2.id
        WHERE m1.entity_id = ? AND m2.entity_id != ?
        GROUP BY e2.name, e2.type
        ORDER BY shared_docs DESC
        LIMIT 20
    """, (entity["id"], entity["id"])).fetchall()

    conn.close()

    return {
        "entity": dict(entity),
        "appearances": [dict(a) for a in appearances],
        "cooccurrences": [dict(c) for c in cooccurrences]
    }