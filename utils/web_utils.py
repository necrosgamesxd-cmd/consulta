"""
Búsqueda web vía DuckDuckGo.
"""

import logging

logger = logging.getLogger(__name__)


def buscar_en_web(query, max_resultados=5):
    """
    Busca información en la web usando DuckDuckGo.
    Retorna una lista de resultados con título, snippet y URL.
    """
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            resultados = []
            for r in ddgs.text(query, max_results=max_resultados):
                resultados.append({
                    "titulo": r.get("title", r.get("titulo", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                    "url": r.get("href", r.get("url", "")),
                })
            return resultados
    except Exception as e:
        logger.error("Error al buscar en web: %s", e)
        return [{"error": f"Error al buscar: {str(e)}"}]
