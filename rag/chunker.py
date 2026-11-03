from typing import List, Dict, Any

def chunk_text(pages_data: List[Dict[str, Any]], chunk_size: int = 400, overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Split extracted document pages into smaller chunks with metadata preservation.
    Returns list of dicts: [{'text': str, 'source': str, 'page': int, 'chunk_id': str}]
    """
    chunks = []
    chunk_counter = 0

    for item in pages_data:
        text = item["text"]
        words = text.split()
        source = item["source"]
        page = item["page"]

        if len(words) <= chunk_size:
            chunk_counter += 1
            chunks.append({
                "text": text,
                "source": source,
                "page": page,
                "chunk_id": f"{source}_p{page}_c{chunk_counter}",
            })
            continue

        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_str = " ".join(words[start:end])
            chunk_counter += 1
            chunks.append({
                "text": chunk_str,
                "source": source,
                "page": page,
                "chunk_id": f"{source}_p{page}_c{chunk_counter}",
            })
            if end >= len(words):
                break
            start += (chunk_size - overlap)

    return chunks

