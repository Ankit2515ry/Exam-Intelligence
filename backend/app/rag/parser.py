"""
PDF Parsing Module

Responsibilities:
-----------------
1. Extract text from PDFs
2. Handle layout-aware extraction
3. OCR fallback for scanned PDFs
4. Clean extracted text
5. Generate structured page-level output

WHY THIS MODULE IS IMPORTANT:
-----------------------------
RAG quality heavily depends on parsing quality.

Bad parsing
→ bad chunks
→ bad embeddings
→ bad retrieval
→ hallucinations

This parser is designed to support:
- metadata filtering
- source citations
- future hierarchical chunking
- OCR-based scanned PDFs
"""

import io
import os
from typing import List, Dict

import fitz
import pytesseract

from PIL import Image

from app.utils.helpers import clean_text


# =========================================================
# TESSERACT CONFIGURATION
# =========================================================

# WINDOWS ONLY
# Comment/remove on Linux or Mac

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


class PDFParser:
    """
    Handles PDF parsing and OCR extraction.
    """

    def __init__(self, file_path: str):

        self.file_path = file_path

    # =====================================================
    # TEXT EXTRACTION
    # =====================================================

    def extract_text_from_page(
        self,
        page
    ) -> str:
        """
        Extract text using layout-aware block parsing.

        WHY BLOCK SORTING?
        ------------------
        PDFs store text in arbitrary positions.

        Sorting blocks by:
        1. vertical position (y)
        2. horizontal position (x)

        helps preserve reading order.
        """

        blocks = page.get_text("blocks")

        # Sort blocks:
        # top-to-bottom
        # left-to-right

        blocks.sort(
            key=lambda block: (
                block[1],
                block[0]
            )
        )

        text = ""

        for block in blocks:

            block_text = block[4]

            text += block_text + "\n"

        return text.strip()

    # =====================================================
    # OCR FALLBACK
    # =====================================================

    def perform_ocr_on_page(
        self,
        page
    ) -> str:
        """
        OCR fallback for scanned PDFs.

        WORKFLOW:
        ---------
        PDF Page
            ↓
        Convert to image
            ↓
        Run Tesseract OCR
            ↓
        Extract text
        """

        pix = page.get_pixmap()

        image_bytes = pix.tobytes("png")

        image = Image.open(
            io.BytesIO(image_bytes)
        )

        ocr_text = pytesseract.image_to_string(
            image
        )

        return ocr_text.strip()

    # =====================================================
    # MAIN PARSER
    # =====================================================

    def parse(self) -> List[Dict]:
        """
        Parse entire PDF document.

        RETURNS:
        --------
        List of page dictionaries.

        Example:
        --------
        [
            {
                "page": 1,
                "text": "...",
                "metadata": {...}
            }
        ]
        """

        doc = fitz.open(self.file_path)

        parsed_pages = []

        document_name = os.path.basename(
            self.file_path
        )

        for page_number in range(len(doc)):

            page = doc.load_page(page_number)

            # Try normal extraction first
            text = self.extract_text_from_page(
                page
            )

            # OCR fallback for scanned PDFs
            if len(text.strip()) < 20:

                print(
                    f"OCR running on page "
                    f"{page_number + 1}"
                )

                text = self.perform_ocr_on_page(
                    page
                )

            # Clean extracted text
            cleaned_text = clean_text(text)

            # Skip empty pages
            if not cleaned_text:
                continue

            # Structured page output
            parsed_pages.append({

                "page": page_number + 1,

                "text": cleaned_text,

                "metadata": {

                    # Original file name
                    "source": document_name,

                    # Page number
                    "page_number": (
                        page_number + 1
                    ),

                    # Future metadata filtering
                    "document_name": document_name
                }
            })

        return parsed_pages