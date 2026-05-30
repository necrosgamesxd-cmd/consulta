"""
Extracción de texto de PDFs con pypdf y fallback OCR via Tesseract.
"""

import io
import logging

logger = logging.getLogger(__name__)


def extraer_texto_pdf(file_bytes):
    """
    Extrae texto de un archivo PDF.
    Si el PDF tiene poco texto (escaneado/imagen), usa OCR con Tesseract.
    """
    try:
        from pypdf import PdfReader
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        texto = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            texto.append(page_text)
        resultado = "\n\n".join(texto).strip()
        if len(resultado) < 50:
            return _ocr_pdf(file_bytes)
        return resultado if resultado else _ocr_pdf(file_bytes)
    except Exception as e:
        logger.warning("Error con pypdf, intentando OCR: %s", e)
        try:
            return _ocr_pdf(file_bytes)
        except Exception as ocr_err:
            logger.error("Error también en OCR: %s", ocr_err)
            return f"Error al extraer texto del PDF: {str(e)}"


def _ocr_pdf(file_bytes):
    """Convierte PDF a imágenes y aplica OCR con Tesseract (español)."""
    from pdf2image import convert_from_bytes
    import pytesseract
    images = convert_from_bytes(file_bytes, dpi=300)
    texto_completo = []
    for img in images:
        texto = pytesseract.image_to_string(img, lang="spa")
        texto_completo.append(texto.strip())
    return "\n\n".join(texto_completo)
