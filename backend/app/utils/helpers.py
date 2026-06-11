import re


def clean_text(text: str) -> str:

    # remove multiple spaces/newlines/tabs
    text = re.sub(r'\s+', ' ', text)

    # remove page numbers like "Page 1"
    text = re.sub(r'Page\s+\d+', '', text)

    # remove extra symbols
    text = re.sub(r'\.{2,}', '.', text)

    # strip spaces
    text = text.strip()

    return text