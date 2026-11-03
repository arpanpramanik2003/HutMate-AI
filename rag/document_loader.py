import io
from typing import List, Dict, Any
from pypdf import PdfReader
from docx import Document

def extract_text_from_file(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """
    Extract text pages/sections from PDF, DOCX, or plain text.
    Returns a list of dicts: [{'text': str, 'page': int, 'source': str}]
    """
    lower_name = filename.lower()
    pages_data = []

    if lower_name.endswith(".pdf"):
        pdf_reader = PdfReader(io.BytesIO(file_bytes))
        for idx, page in enumerate(pdf_reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages_data.append({
                    "text": text.strip(),
                    "page": idx,
                    "source": filename,
                })

    elif lower_name.endswith(".docx"):
        doc = Document(io.BytesIO(file_bytes))
        full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        if full_text.strip():
            pages_data.append({
                "text": full_text.strip(),
                "page": 1,
                "source": filename,
            })

    elif lower_name.endswith(".txt"):
        text = file_bytes.decode("utf-8", errors="ignore")
        if text.strip():
            pages_data.append({
                "text": text.strip(),
                "page": 1,
                "source": filename,
            })
    else:
        raise ValueError(f"Unsupported file type: {filename}. Supported formats: PDF, DOCX, TXT")

    return pages_data

