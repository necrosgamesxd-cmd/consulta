"""
Cálculos financieros: valor UF, límite de crédito.
"""

import time
import requests
import logging

logger = logging.getLogger(__name__)

VALOR_UF_FALLBACK = 38000
_uf_cache = {"value": VALOR_UF_FALLBACK, "timestamp": 0}


def obtener_valor_uf():
    """
    Obtiene el valor actual de la UF desde mindicador.cl.
    Cache de 1 hora para no sobrecargar la API.
    Si falla, retorna el valor de respaldo.
    """
    now = time.time()
    if now - _uf_cache["timestamp"] > 3600:
        try:
            resp = requests.get("https://mindicador.cl/api/uf", timeout=10)
            data = resp.json()
            serie = data.get("serie", [])
            if serie:
                _uf_cache["value"] = serie[0].get("valor", VALOR_UF_FALLBACK)
                _uf_cache["timestamp"] = now
        except Exception as e:
            logger.warning("Error al obtener UF, usando cache/fallback: %s", e)
    return round(_uf_cache["value"], 0)


def calcular_limite_uf(ingresos_totales):
    """
    Calcula el máximo de UF que un cliente puede pagar según sus ingresos totales mensuales.
    Fórmula: (ingresos_totales / 625) + 200 = límite UF
    """
    return (ingresos_totales / 625) + 200
