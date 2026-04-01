# Written by V
from fastapi import APIRouter, Query
from db.sqlite_client import get_connection
from fastapi.responses import Response

router = APIRouter()

@router.get("/")
def get_changelog(limit: int = Query(20, le=100)):
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM releases
        ORDER BY run_date DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return {"releases": [dict(r) for r in rows]}

@router.get("/rss")
def get_rss():
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM releases
        ORDER BY run_date DESC
        LIMIT 20
    """).fetchall()
    conn.close()

    items = ""
    for r in rows:
        items += f"""
        <item>
            <title>{r['corpus'].upper()} - {r['docs_added']} docs added</title>
            <description>{r['notes']}</description>
            <pubDate>{r['run_date']}</pubDate>
        </item>"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Devil Has Many Faces - Changelog</title>
        <link>https://devil-has-many-faces.com</link>
        <description>New document releases and updates</description>
        {items}
    </channel>
</rss>"""

    return Response(content=rss, media_type="application/xml")