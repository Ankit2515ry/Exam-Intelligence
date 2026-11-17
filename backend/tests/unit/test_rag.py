from types import SimpleNamespace
from unittest.mock import Mock

from langchain_core.documents import Document
import pytest


pytestmark = pytest.mark.unit


def test_cleaning_and_chunk_metadata():
    from app.rag.chunker import create_chunks
    from app.utils.helpers import clean_text
    assert clean_text("Page 1\n A\t B... ") == "A B."
    chunks = create_chunks([{"page": 3, "text": "Relational database normalization reduces redundancy. " * 12}], "uuid", 9)
    assert len(chunks) > 1
    assert len({chunk["chunk_id"] for chunk in chunks}) == len(chunks)
    assert [chunk["chunk_index"] for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk["metadata"]["user_id"] == 9 and chunk["page"] == 3 for chunk in chunks)
    assert all(chunk["document_id"] == "uuid" for chunk in chunks)
    assert create_chunks([{"page": 1, "text": "tiny"}], "uuid", 9) == []


def test_embedding_empty_inputs_and_normalization():
    from app.rag.embedder import generate_embedding, generate_embeddings
    assert generate_embedding(" ") == []
    assert generate_embeddings(["", " "]) == []
    vectors = generate_embeddings(["normalization", "indexing"])
    assert len(vectors) == 2
    assert sum(value ** 2 for value in vectors[0]) == pytest.approx(1)
    assert generate_embedding("normalization") == vectors[0]


def test_bm25_hybrid_and_reranking(monkeypatch):
    from app.rag.bm25 import bm25_search
    from app.rag.hybrid_search import combine_scores
    from app.rag import reranker
    chunks = [Document(page_content=f"normalization table {index}", metadata={"score": 0.8}) for index in range(10)]
    keywords = bm25_search("normalization", chunks)
    assert len(keywords) == 5
    combined = combine_scores(keywords)
    assert all("hybrid_score" in chunk.metadata for chunk in combined)
    monkeypatch.setattr(reranker.reranker_model, "predict", Mock(return_value=[0, 1, 2, 3, 4]))
    ranked = reranker.rerank("normalization", combined)
    assert [chunk.metadata["rerank_score"] for chunk in ranked] == [4, 3, 2, 1, 0]


def test_empty_ranking_stages_and_zero_scores():
    from app.rag.bm25 import bm25_search
    from app.rag.hybrid_search import combine_scores
    from app.rag.reranker import rerank
    assert bm25_search("q", []) == combine_scores([]) == rerank("q", []) == []
    chunk = Document(page_content="text", metadata={"score": 0, "bm25_score": 0})
    assert combine_scores([chunk])[0].metadata["hybrid_score"] == 0


def test_prompt_includes_context_and_general_knowledge_policy():
    from app.rag.prompt_builder import build_prompt
    prompt = build_prompt("Explain normalization", [Document(page_content="Synthetic evidence")])
    assert "Synthetic evidence" in prompt and "Explain normalization" in prompt
    assert "general knowledge" in prompt


@pytest.mark.parametrize("result,expected", [
    (SimpleNamespace(text="answer"), "answer"),
    (SimpleNamespace(text=""), "Unable to generate response."),
    (RuntimeError("synthetic failure"), "An error occurred while generating the response."),
])
def test_llm_response_and_failure_contract(monkeypatch, result, expected):
    from app.rag import llm_service
    model = Mock()
    if isinstance(result, Exception):
        model.generate_content.side_effect = result
    else:
        model.generate_content.return_value = result
    monkeypatch.setattr(llm_service, "model", model)
    assert llm_service.generate_answer("test prompt") == expected


def test_parser_extracts_generated_pdf_without_ocr(pdf_bytes, tmp_path, monkeypatch):
    from app.rag.parser import PDFParser
    path = tmp_path / "synthetic.pdf"
    path.write_bytes(pdf_bytes)
    ocr = Mock(side_effect=AssertionError("Text PDF must not require OCR"))
    monkeypatch.setattr(PDFParser, "perform_ocr_on_page", ocr)
    pages = PDFParser(str(path)).parse()
    ocr.assert_not_called()
    assert len(pages) == 1
    assert pages[0]["page"] == 1
    assert pages[0]["metadata"]["page_number"] == 1
    assert "normalization" in pages[0]["text"]


def test_parser_ocr_fallback_is_mocked(monkeypatch, tmp_path):
    import fitz
    from app.rag.parser import PDFParser
    path = tmp_path / "blank.pdf"
    with fitz.open() as document:
        document.new_page()
        document.save(path)
    ocr = Mock(return_value="Synthetic OCR text with enough characters for a useful passage.")
    monkeypatch.setattr(PDFParser, "perform_ocr_on_page", ocr)
    pages = PDFParser(str(path)).parse()
    ocr.assert_called_once()
    assert pages[0]["page"] == 1
    assert pages[0]["metadata"]["page_number"] == 1
    assert pages[0]["text"].startswith("Synthetic OCR")


def test_missing_tesseract_has_clear_error_when_ocr_is_required(monkeypatch, tmp_path):
    import fitz
    from app.rag import parser

    path = tmp_path / "scanned.pdf"
    with fitz.open() as document:
        document.new_page()
        document.save(path)

    missing = parser.pytesseract.TesseractNotFoundError()
    monkeypatch.setattr(
        parser.pytesseract,
        "image_to_string",
        Mock(side_effect=missing),
    )

    with pytest.raises(RuntimeError, match="OCR is required on page 1") as error:
        parser.PDFParser(str(path)).parse()
    assert "TESSERACT_CMD" in str(error.value)
    assert "PATH" in str(error.value)


def test_tesseract_configuration_uses_explicit_path_or_system_path(monkeypatch):
    from app.rag import parser

    original = parser.pytesseract.pytesseract.tesseract_cmd
    try:
        parser._configure_tesseract(None)
        assert parser.pytesseract.pytesseract.tesseract_cmd == "tesseract"
        parser._configure_tesseract("/opt/tesseract/bin/tesseract")
        assert parser.pytesseract.pytesseract.tesseract_cmd == "/opt/tesseract/bin/tesseract"
    finally:
        parser.pytesseract.pytesseract.tesseract_cmd = original
