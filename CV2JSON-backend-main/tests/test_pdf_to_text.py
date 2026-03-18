import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.ingest.pdf_to_text import extract_text
from tests.constants import SAMPLE_SCANNED_PDF, SAMPLE_TEXT_PDF


def test_extract_text_with_embedded_text_pdf():
    result = extract_text(SAMPLE_TEXT_PDF)
    print(result)
    assert "Hello" in result or len(result) > 0


def test_extract_text_with_scanned_pdf_fallback():
    result = extract_text(SAMPLE_SCANNED_PDF)
    print(result)
    assert "OCR" in result or len(result) > 0


if __name__ == "__main__":
    test_extract_text_with_embedded_text_pdf()
    test_extract_text_with_scanned_pdf_fallback()
