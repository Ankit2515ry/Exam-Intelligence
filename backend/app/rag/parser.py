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
from app.config.settings import TESSERACT_CMD
from app.observability.performance import stage, set_value


# =========================================================
# TESSERACT CONFIGURATION
# =========================================================

def _configure_tesseract(command: str | None) -> None:
    # pytesseract resolves this command through PATH when no explicit path is set.
    pytesseract.pytesseract.tesseract_cmd = command or "tesseract"


_configure_tesseract(TESSERACT_CMD)




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
        page,
        page_number: int | None = None
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

        pixmap = page.get_pixmap()

        try:
            image_bytes = pixmap.tobytes("png")

            with io.BytesIO(image_bytes) as image_stream:
                with Image.open(image_stream) as image:
                    try:
                        set_value("ocr_used", True)
                        with stage("ocr"):
                            ocr_text = pytesseract.image_to_string(image)
                    except pytesseract.TesseractNotFoundError as exc:
                        page_label = (
                            f" on page {page_number}"
                            if page_number is not None
                            else ""
                        )
                        raise RuntimeError(
                            "OCR is required"
                            f"{page_label}, but Tesseract was not found. "
                            "Install Tesseract and add it to PATH, or set "
                            "TESSERACT_CMD to its executable path."
                        ) from exc

            return ocr_text.strip()
        finally:
            pixmap = None

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

        parsed_pages = []

        document_name = os.path.basename(
            self.file_path
        )

        with fitz.open(self.file_path) as doc:
            for page_number in range(len(doc)):

                page = doc.load_page(page_number)

                # Try normal extraction first
                text = self.extract_text_from_page(
                    page
                )

                # OCR fallback for scanned PDFs
                if len(text.strip()) < 20:

                    text = self.perform_ocr_on_page(
                        page,
                        page_number=page_number + 1
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
