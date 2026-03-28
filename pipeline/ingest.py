import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extractor import extract_document
from ner import extract_entities

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.db.sqlite_client import get_connection
from backend.db.mongo_client import get_db

CORPORA = {
    "epstein": "data/raw/epstein",
    "jfk": "data/raw/jfk"
}

def get_text_based_pdfs(folder):
    import fitz
    results = []
    for f in os.listdir(folder):
        if not f.endswith(".pdf"):
            continue
        path = os.path.join(folder, f)
        try:
            doc = fitz.open(path)
            text = doc[0].get_text("text").strip()
            doc.close()
            if len(text) > 50:
                results.append(path)
        except:
            pass
    return results

def doc_already_ingested(conn, filename):
    row = conn.execute(
        "SELECT id FROM documents WHERE filename = ?", (filename,)
    ).fetchone()
    return row is not None

def ingest_document(file_path, corpus, conn, db):
    filename = os.path.basename(file_path)

    if doc_already_ingested(conn, filename):
        return "skipped"

    result = extract_document(file_path, corpus)

    if result is None or result.get("is_scanned"):
        return "scanned"

    if result["page_count"] == 0:
        return "empty"

    # Write to MongoDB
    try:
        db.raw_docs.insert_one({
            "doc_id": result["doc_id"],
            "corpus": corpus,
            "filename": filename,
            "file_path": file_path,
            "page_count": result["page_count"],
            "pages": result["pages"]
        })
    except Exception as e:
        print(f"    Mongo error: {e}")
        return "error"

    # Write to SQLite documents table
    conn.execute("""
        INSERT OR IGNORE INTO documents
        (id, corpus, filename, file_path, page_count, is_scanned)
        VALUES (?, ?, ?, ?, ?, 0)
    """, (result["doc_id"], corpus, filename, file_path, result["page_count"]))

    # Write redactions
    for page in result["pages"]:
        if page["redaction_count"] > 0:
            conn.execute("""
                INSERT INTO redactions
                (doc_id, page_num, redaction_count, estimated_chars)
                VALUES (?, ?, ?, ?)
            """, (result["doc_id"], page["page_num"],
                  page["redaction_count"], page["estimated_chars_redacted"]))

    # Write FTS index
    for page in result["pages"]:
        if page["text"]:
            conn.execute("""
                INSERT INTO documents_fts (doc_id, page_num, text)
                VALUES (?, ?, ?)
            """, (result["doc_id"], page["page_num"], page["text"]))

    # Run NER and write entities
    mentions = extract_entities(result["pages"])
    entities_added = 0

    for mention in mentions:
        # Upsert entity
        conn.execute("""
            INSERT OR IGNORE INTO entities (name, type)
            VALUES (?, ?)
        """, (mention["name"], mention["type"]))

        entity_row = conn.execute("""
            SELECT id FROM entities WHERE name = ? AND type = ?
        """, (mention["name"], mention["type"])).fetchone()

        if entity_row:
            conn.execute("""
                INSERT INTO mentions (entity_id, doc_id, page_num, context)
                VALUES (?, ?, ?, ?)
            """, (entity_row["id"], result["doc_id"],
                  mention["page_num"], mention["context"]))
            entities_added += 1

    conn.commit()
    return f"ok:{result['page_count']}p:{entities_added}e"

def run_ingestion():
    conn = get_connection()
    db = get_db()

    total_docs = 0
    total_skipped = 0
    total_errors = 0
    start_time = datetime.now()

    for corpus, folder in CORPORA.items():
        print(f"\n{'='*50}")
        print(f"Processing corpus: {corpus.upper()}")
        print(f"{'='*50}")

        pdfs = get_text_based_pdfs(folder)
        print(f"Found {len(pdfs)} text-based PDFs\n")

        docs_added = 0
        entities_found = 0

        for i, path in enumerate(pdfs):
            filename = os.path.basename(path)
            print(f"  [{i+1}/{len(pdfs)}] {filename}", end=" ... ")

            status = ingest_document(path, corpus, conn, db)
            print(status)

            if status.startswith("ok"):
                parts = status.split(":")
                docs_added += 1
                total_docs += 1
                if len(parts) > 2:
                    entities_found += int(parts[2].replace("e", ""))
            elif status == "skipped":
                total_skipped += 1
            elif status == "error":
                total_errors += 1

            if (i + 1) % 50 == 0:
                print(f"\n  Progress: {i+1}/{len(pdfs)} processed\n")

        # Log to releases table
        conn.execute("""
            INSERT INTO releases (corpus, docs_added, entities_found, notes)
            VALUES (?, ?, ?, ?)
        """, (corpus, docs_added, entities_found,
              f"Ingestion run {start_time.strftime('%Y-%m-%d %H:%M')}"))
        conn.commit()

        print(f"\n  Corpus done: {docs_added} docs, {entities_found} entities")

    elapsed = (datetime.now() - start_time).seconds
    print(f"\n{'='*50}")
    print(f"INGESTION COMPLETE")
    print(f"Total docs: {total_docs}")
    print(f"Skipped: {total_skipped}")
    print(f"Errors: {total_errors}")
    print(f"Time: {elapsed}s")
    print(f"{'='*50}")

    conn.close()

if __name__ == "__main__":
    print("Starting ingestion process...")
    run_ingestion()