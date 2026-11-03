from pathlib import Path
from typing import List, Dict, Any
from core import config
from rag.embeddings import generate_embeddings

COLLECTION_NAME = "restaurant_knowledge"

_chroma_client = None


def get_chroma_client():
    """Return singleton local persistent ChromaDB client (lazily imported for fast server boot)."""
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=config.CHROMA_DB_DIR)
    return _chroma_client


def get_or_create_collection():
    """Get or create the restaurant knowledge collection in ChromaDB."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def index_chunks(chunks: List[Dict[str, Any]]):
    """Generate embeddings and store chunks with metadata in ChromaDB."""
    if not chunks:
        return

    collection = get_or_create_collection()
    texts = [c["text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [{"source": c["source"], "page": c["page"]} for c in chunks]
    embeddings = generate_embeddings(texts)

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def retrieve_relevant_chunks(query: str, n_results: int = 3) -> List[Dict[str, Any]]:
    """Retrieve the most relevant document chunks for a given query."""
    collection = get_or_create_collection()
    if collection.count() == 0:
        return []
    query_vector = generate_embeddings([query])[0]

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
    )

    retrieved = []
    if results and "documents" in results and results["documents"]:
        docs = results["documents"][0]
        metas = results["metadatas"][0] if "metadatas" in results else []
        dists = results["distances"][0] if "distances" in results else []

        for idx, doc in enumerate(docs):
            meta = metas[idx] if idx < len(metas) else {}
            dist = dists[idx] if idx < len(dists) else 1.0
            retrieved.append({
                "text": doc,
                "source": meta.get("source", "Unknown"),
                "page": meta.get("page", 1),
                "distance": dist,
            })

    return retrieved


def count_indexed_documents() -> int:
    """Return the total number of chunks currently indexed in ChromaDB."""
    sqlite_file = Path(config.CHROMA_DB_DIR) / "chroma.sqlite3"
    if not sqlite_file.exists() and _chroma_client is None:
        return 0
    try:
        collection = get_or_create_collection()
        return collection.count()
    except Exception:
        return 0
