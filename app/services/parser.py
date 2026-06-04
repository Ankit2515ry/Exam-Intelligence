# import fitz
# import pytesseract
# from PIL import Image
# import io
# import os

# # FOR WINDOWS ONLY
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# class PDFParser:

#     def __init__(self, file_path):
#         self.file_path = file_path

#     def extract_text_from_page(self, page):

#         blocks = page.get_text("blocks")

#         # Sort blocks:
#         # first by vertical position (y)
#         # then horizontal position (x)
#         blocks.sort(key=lambda b: (b[1], b[0]))

#         text = ""

#         for block in blocks:

#             block_text = block[4]

#             text += block_text + "\n"

#         return text.strip()

#     def perform_ocr_on_page(self, page):
#         """
#         OCR fallback for scanned PDFs
#         """
#         pix = page.get_pixmap()

#         image_bytes = pix.tobytes("png")

#         image = Image.open(io.BytesIO(image_bytes))

#         ocr_text = pytesseract.image_to_string(image)

#         return ocr_text.strip()

#     def clean_text(self, text):
#         """
#         Basic text cleaning
#         """

#         text = text.replace("\n", " ")

#         text = " ".join(text.split())

#         return text

#     def parse(self):

#         doc = fitz.open(self.file_path)

#         parsed_pages = []

#         for page_number in range(len(doc)):

#             page = doc.load_page(page_number)

#             text = self.extract_text_from_page(page)

#             # If no text found -> OCR
#             if len(text.strip()) < 20:
#                 print(f"OCR running on page {page_number + 1}")
#                 text = self.perform_ocr_on_page(page)

#             cleaned_text = self.clean_text(text)

#             parsed_pages.append({
#                 "page": page_number + 1,
#                 "content": cleaned_text,
#                 "metadata": {
#                     "source": os.path.basename(self.file_path),
#                     "page_number": page_number + 1
#                 }
#             })

#         return parsed_pages
    
import fitz
import pytesseract
from PIL import Image

import io
import os

from app.utils.helpers import clean_text


# WINDOWS ONLY
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


class PDFParser:

    def __init__(self, file_path):

        self.file_path = file_path

    def extract_text_from_page(self, page):

        blocks = page.get_text("blocks")

        blocks.sort(
            key=lambda b: (b[1], b[0])
        )

        text = ""

        for block in blocks:

            block_text = block[4]

            text += block_text + "\n"

        return text.strip()

    def perform_ocr_on_page(self, page):

        pix = page.get_pixmap()

        image_bytes = pix.tobytes("png")

        image = Image.open(
            io.BytesIO(image_bytes)
        )

        ocr_text = pytesseract.image_to_string(
            image
        )

        return ocr_text.strip()
    
    def parse(self):

        doc = fitz.open(self.file_path)

        parsed_pages = []

        for page_number in range(len(doc)):

            page = doc.load_page(page_number)

            text = self.extract_text_from_page(page)

            # OCR fallback
            if len(text.strip()) < 20:

                print(
                    f"OCR running on page {page_number + 1}"
                )

                text = self.perform_ocr_on_page(page)

            cleaned_text = clean_text(text)

            parsed_pages.append({

                "page": page_number + 1,

                "text": cleaned_text,

                "metadata": {

                    "source": os.path.basename(
                        self.file_path
                    ),

                    "page_number": page_number + 1
                }
            })

        return parsed_pages