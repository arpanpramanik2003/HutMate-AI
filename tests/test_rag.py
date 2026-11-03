import pytest
from rag.document_loader import extract_text_from_file
from rag.chunker import chunk_text
from rag.retriever import index_chunks, retrieve_relevant_chunks

def test_document_extraction_and_chunking():
    sample_text = b"Food Safety Policy: Ensure cold storage is maintained at 4C or below."
    pages = extract_text_from_file(sample_text, "test_policy.txt")
    assert len(pages) == 1
    assert "Food Safety Policy" in pages[0]["text"]

    chunks = chunk_text(pages, chunk_size=20, overlap=5)
    assert len(chunks) >= 1
    assert chunks[0]["source"] == "test_policy.txt"

def test_rag_indexing_and_retrieval():
    sample_text = b"Chicken Biryani Recipe: Marinate 1 kg chicken with curd, garam masala, and ginger-garlic paste."
    pages = extract_text_from_file(sample_text, "biryani_recipe.txt")
    chunks = chunk_text(pages)
    index_chunks(chunks)

    results = retrieve_relevant_chunks("biryani ingredients", n_results=1)
    assert len(results) > 0
    assert "biryani" in results[0]["text"].lower()

