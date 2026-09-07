import abc
import shutil
from typing import Dict, Any, List, Optional, Tuple


class BaseOCRProvider(abc.ABC):
    @abc.abstractmethod
    def is_available(self) -> bool:
        """Returns True if the OCR engine is available."""
        pass

    @abc.abstractmethod
    def extract_page_ocr(self, page_pixmap_bytes: bytes) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Runs OCR on page image bytes.
        Returns:
            text: Full text extracted from OCR
            blocks: List of block dictionaries with bbox and text
        """
        pass


class TesseractOCRProvider(BaseOCRProvider):
    def __init__(self):
        self._available = bool(shutil.which("tesseract"))

    def is_available(self) -> bool:
        return self._available

    def extract_page_ocr(self, page_pixmap_bytes: bytes) -> Tuple[str, List[Dict[str, Any]]]:
        if not self._available:
            return "", []
        try:
            import pytesseract
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(page_pixmap_bytes))
            text = pytesseract.image_to_string(image)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            blocks = []
            n_boxes = len(data['level'])
            for i in range(n_boxes):
                word = data['text'][i].strip()
                if word:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    blocks.append({
                        "text": word,
                        "bbox": [x, y, x + w, y + h],
                        "type": "ocr_word",
                        "confidence": float(data['conf'][i]) / 100.0 if data['conf'][i] != '-1' else 0.5
                    })
            return text, blocks
        except Exception as e:
            print(f"[OCR] Tesseract error: {e}")
            return "", []


class FallbackOCRProvider(BaseOCRProvider):
    """Graceful fallback when no external OCR engine is installed."""
    def is_available(self) -> bool:
        return False

    def extract_page_ocr(self, page_pixmap_bytes: bytes) -> Tuple[str, List[Dict[str, Any]]]:
        return "", []


def get_ocr_provider() -> BaseOCRProvider:
    provider = TesseractOCRProvider()
    if provider.is_available():
        return provider
    return FallbackOCRProvider()
