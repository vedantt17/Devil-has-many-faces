import fitz
import os
import uuid
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io
from dotenv import load_dotenv
import time

load_dotenv()

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def is_scanned(page) -> bool:
    text = page.get_text("text").strip()
    return len(text) < 50

def preprocess_image(image_bytes: bytes) -> np.ndarray:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Scale up for better OCR
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, h=30)

    # Increase contrast
    gray = cv2.equalizeHist(gray)

    # Threshold to pure black and white
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return binary

def ocr_page(image_bytes: bytes, page_num: int) -> str:
    try:
        processed = preprocess_image(image_bytes)
        pil_image = Image.fromarray(processed)
        custom_config = r"--oem 3 --psm 6 -l eng"
        text = pytesseract.image_to_string(pil_image, config=custom_config)
        return text.strip()
    except Exception as e:
        print(f"    OCR error on page {page_num}: {e}")
        return ""

def page_to_image(page) -> bytes:
    mat = fitz.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=mat)
    return pix.tobytes("png")

def extract_document(file_path: str, corpus: str) -> dict:
    filename = os.path.basename(file_path)
    doc_id = str(uuid.uuid4())

    doc = fitz.open(file_path)
    pages = []
    total_redactions = 0

    first_page = doc[0]
    scanned = is_scanned(first_page)

    if scanned:
        print(f"  Scanned PDF, using enhanced OCR: {filename}")

    for page_num in range(len(doc)):
        page = doc[page_num]

        if scanned:
            image_bytes = page_to_image(page)
            text = ocr_page(image_bytes, page_num + 1)
        else:
            text = page.get_text("text").strip()

        # Detect redactions
        redaction_count = 0
        estimated_chars = 0

        for annot in page.annots():
            if annot.type[0] == 12:
                redaction_count += 1
                rect = annot.rect
                estimated_chars += int((rect.width / 7) * (rect.height / 12))

        drawings = page.get_drawings()
        for drawing in drawings:
            if drawing.get("fill") in [(0, 0, 0), (0.0, 0.0, 0.0)]:
                rect = drawing.get("rect")
                if rect and rect.width > 20 and rect.height > 8:
                    redaction_count += 1
                    estimated_chars += int((rect.width / 7) * (rect.height / 12))

        total_redactions += redaction_count

        pages.append({
            "page_num": page_num + 1,
            "text": text,
            "redaction_count": redaction_count,
            "estimated_chars_redacted": estimated_chars,
            "word_count": len(text.split()) if text else 0
        })

    doc.close()

    return {
        "doc_id": doc_id,
        "corpus": corpus,
        "filename": filename,
        "file_path": file_path,
        "page_count": len(pages),
        "total_redactions": total_redactions,
        "pages": pages
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python extractor.py <file_path> <corpus>")
        sys.exit(1)

    result = extract_document(sys.argv[1], sys.argv[2])
    print(f"Doc ID: {result['doc_id']}")
    print(f"Pages: {result['page_count']}")
    print(f"Total redactions: {result['total_redactions']}")
    for p in result['pages'][:2]:
        print(f"\n--- Page {p['page_num']} ---")
        print(f"Words: {p['word_count']}, Redactions: {p['redaction_count']}")
        print(p['text'][:400])