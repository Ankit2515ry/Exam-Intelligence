import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.utils.helpers import clean_text


CHUNK_SIZE = 500

CHUNK_OVERLAP = 100


def create_chunks(pages, document_id):

    splitter = RecursiveCharacterTextSplitter(

        chunk_size=CHUNK_SIZE,

        chunk_overlap=CHUNK_OVERLAP,

        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
        ]
    )

    chunks = []

    chunk_index = 0

    for page_data in pages:

        page_num = page_data["page"]

        raw_text = page_data["text"]

        text = clean_text(raw_text)

        # skip empty pages
        if not text:
            continue

        split_texts = splitter.split_text(text)

        for split in split_texts:

            # skip tiny chunks
            if len(split.strip()) < 30:
                continue

            chunk = {

                "chunk_id": str(uuid.uuid4()),

                "document_id": document_id,

                "text": split,

                "page": page_num,

                "chunk_index": chunk_index
            }

            chunks.append(chunk)

            chunk_index += 1

    return chunks