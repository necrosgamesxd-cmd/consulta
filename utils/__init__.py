"""
Utilidades para integración con proveedores de AI, finanzas, PDF y búsqueda web.
"""

from utils.logging_setup import setup_logging

setup_logging()

from utils.finanzas import (
    VALOR_UF_FALLBACK,
    obtener_valor_uf,
    calcular_limite_uf,
)

from utils.web_utils import buscar_en_web

from utils.pdf_utils import extraer_texto_pdf, _ocr_pdf

from utils.ai import (
    PROVIDERS,
    DEFAULT_PROVIDER,
    MODEL_NANO_OMNI,
    MODEL_SUPER,
    get_active_provider,
    get_provider_config,
    get_model_for_provider,
    _acumular_usage,
    _get_api_key,
    get_ai_client,
    get_openai_client,
    verificar_api_key,
    analizar_proyecto_por_nombre,
    generar_descripcion_con_ai,
    analizar_pdf_con_ai,
    analizar_cotizacion_con_ai,
    generar_recomendacion_inicial,
    analizar_excel_promociones,
    chat_stream,
)
