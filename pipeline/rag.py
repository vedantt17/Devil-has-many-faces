# Written by V
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.db.mongo_client import get_db
from groq import Groq
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma_db")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)
embedder = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

COLLECTION_NAME = "dmf_chunks"

def get_collection():
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def build_vector_store():
    db = get_db()
    collection = get_collection()

    existing = set(collection.get()["ids"])
    print(f"Existing chunks in ChromaDB: {len(existing)}")

    docs = list(db.raw_docs.find({}, {
        "doc_id": 1, "corpus": 1, "filename": 1, "pages": 1
    }))

    print(f"Processing {len(docs)} documents...")

    total_chunks = 0
    batch_ids = []
    batch_embeddings = []
    batch_docs = []
    batch_metas = []
    BATCH_SIZE = 100

    for doc_idx, doc in enumerate(docs):
        for page in doc.get("pages", []):
            text = page.get("text", "").strip()
            if not text:
                continue

            chunks = chunk_text(text)
            for chunk_idx, chunk in enumerate(chunks):
                chunk_id = f"{doc['doc_id']}_{page['page_num']}_{chunk_idx}"

                if chunk_id in existing:
                    continue

                embedding = embedder.encode(chunk).tolist()

                batch_ids.append(chunk_id)
                batch_embeddings.append(embedding)
                batch_docs.append(chunk)
                batch_metas.append({
                    "doc_id": doc["doc_id"],
                    "corpus": doc["corpus"],
                    "filename": doc["filename"],
                    "page_num": page["page_num"]
                })
                total_chunks += 1

                if len(batch_ids) >= BATCH_SIZE:
                    collection.add(
                        ids=batch_ids,
                        embeddings=batch_embeddings,
                        documents=batch_docs,
                        metadatas=batch_metas
                    )
                    batch_ids, batch_embeddings, batch_docs, batch_metas = [], [], [], []
                    print(f"  Stored {total_chunks} chunks so far...")

        if (doc_idx + 1) % 100 == 0:
            print(f"  Processed {doc_idx + 1}/{len(docs)} documents")

    if batch_ids:
        collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_docs,
            metadatas=batch_metas
        )

    print(f"\nVector store built. Total chunks: {total_chunks}")

def retrieve(query: str, top_k: int = 5, corpus: str = None) -> list:
    collection = get_collection()
    query_embedding = embedder.encode(query).tolist()

    where = {"corpus": corpus} if corpus else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append({
            "chunk_id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })

    return chunks

def answer(query: str, corpus: str = None) -> dict:
    chunks = retrieve(query, top_k=5, corpus=corpus)

    if not chunks:
        return {
            "answer": "No relevant documents found.",
            "citations": []
        }

    context = ""
    for i, chunk in enumerate(chunks):
        meta = chunk["metadata"]
        context += f"\n[Source {i+1}: {meta['filename']}, page {meta['page_num']}]\n"
        context += chunk["text"] + "\n"

    prompt = f"""Answer the question using ONLY the provided source documents.
For every claim you make, cite the source number in brackets like [Source 1].
If the answer is not in the documents, say "This information was not found in the available documents."
Do not use any outside knowledge.

Question: {query}

Sources:
{context}

Answer:"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an analyst of declassified government documents. Answer questions using ONLY the provided source documents. Cite sources using [Source N] notation. If the answer is not in the documents, say so."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000,
            temperature=0.1
        )
        answer_text = response.choices[0].message.content.strip()
    except Exception as e:
        answer_text = f"Error generating answer: {e}"

    citations = []
    for chunk in chunks:
        meta = chunk["metadata"]
        citations.append({
            "filename": meta["filename"],
            "page_num": meta["page_num"],
            "corpus": meta["corpus"],
            "doc_id": meta["doc_id"],
            "excerpt": chunk["text"][:200]
        })

    return {
        "answer": answer_text,
        "citations": citations
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build_vector_store()
    elif len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Query: {query}\n")
        result = answer(query)
        print("Answer:")
        print(result["answer"])
        print("\nCitations:")
        for c in result["citations"]:
            print(f"  - {c['filename']} page {c['page_num']}")
    else:
        print("Usage:")
        print("  python rag.py build          # build vector store")
        print("  python rag.py <question>     # ask a question")