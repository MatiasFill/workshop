from pathlib import Path

def ocr_available():
    try:
        import pytesseract
        return True
    except Exception:
        return False

def extract_image_text(data: bytes):
    try:
        from PIL import Image
        import pytesseract
        from io import BytesIO
        image = Image.open(BytesIO(data))
        return pytesseract.image_to_string(image, lang="por+eng")
    except Exception as exc:
        return f"OCR indisponível: {exc}"
