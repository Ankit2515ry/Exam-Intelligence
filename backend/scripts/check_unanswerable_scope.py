"""
Verify unanswerable candidate questions against full document scopes.
"""
import fitz
import re
from pathlib import Path

corpus_dir = Path("backend/evaluation/corpus/corpus-v1")

def search_doc(pdf_name, keywords):
    doc = fitz.open(corpus_dir / pdf_name)
    full_text = " ".join(doc.load_page(i).get_text() for i in range(doc.page_count)).lower()
    print(f"=== Searching {pdf_name} ({doc.page_count} pages, {len(full_text)} chars) ===")
    for kw in keywords:
        count = full_text.count(kw.lower())
        print(f"  Keyword '{kw}': {count} occurrences")

if __name__ == "__main__":
    search_doc("10 RAG Architectures.pdf", ["Gemini", "revenue", "2025", "worldwide", "Google"])
    search_doc("DBMS.pdf", ["password", "author", "private password", "PostgreSQL", "MongoDB", "NoSQL", "Redis"])
