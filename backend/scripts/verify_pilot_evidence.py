"""
Inspect text on cited pages of evaluation PDFs for pilot questions Q01-Q15.
"""
import fitz
import json
import re
from pathlib import Path

corpus_dir = Path("backend/evaluation/corpus/corpus-v1")

def inspect_doc_pages(pdf_name, pages):
    doc = fitz.open(corpus_dir / pdf_name)
    for p in pages:
        page = doc.load_page(p - 1)
        text = page.get_text()
        print(f"\n################ {pdf_name} - Page {p} (length {len(text)}) ################")
        print(text[:1500])
        if len(text) > 1500:
            print("... [TRUNCATED] ...")
            print(text[-500:])

if __name__ == "__main__":
    print("--- 10 RAG Architectures.pdf ---")
    inspect_doc_pages("10 RAG Architectures.pdf", [1, 3, 4, 5, 7, 8])

    print("\n--- DBMS.pdf ---")
    inspect_doc_pages("DBMS.pdf", [2, 5, 6, 8])

    print("\n--- Operating-Systems.pdf ---")
    inspect_doc_pages("Operating-Systems.pdf", [6, 7, 8, 9, 10, 11])
