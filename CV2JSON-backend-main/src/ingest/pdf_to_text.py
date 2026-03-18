import logging
import os
import tempfile

import easyocr
import pdfplumber
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


def extract_text(path: str) -> str:
    """
    Extract text from a PDF.
    First try pdfplumber (embedded text).
    If none found, fallback to EasyOCR.
    """
    text = ""

    # Step 1: Try pdfplumber
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        logger.error(f"pdfplumber failed on {path}: {e}")

    # Step 2: OCR fallback
    if not text.strip():
        logger.info(f"No embedded text in {path}, using OCR fallback...")
        text = ocr_with_easyocr(path)

    return text.strip()


def ocr_with_easyocr(path: str, lang_list=None) -> str:
    """
    Converts PDF pages to images and extracts text.
    """
    if lang_list is None:
        lang_list = ["en"]  # Example: ["en", "ur"] for English + Urdu

    text = ""
    reader = easyocr.Reader(lang_list)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            images = convert_from_path(path, output_folder=temp_dir)
            for i, image in enumerate(images):
                img_path = os.path.join(temp_dir, f"page_{i}.png")
                image.save(img_path, "PNG")
                results = reader.readtext(img_path, detail=0)
                text += "\n".join(results) + "\n"
    except Exception as e:
        logger.error(f"EasyOCR failed on {path}: {e}")

    return text.strip()
