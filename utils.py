"""
Utilidades para integración con proveedores de AI (OpenRouter, Grok, Gemini) y búsqueda web.
"""

import os
import io
import time
import requests
from collections import defaultdict
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from storage import get_promociones

load_dotenv()

# ========== CONFIGURACIÓN DE PROVEEDORES ==========
PROVIDERS = {
    "openrouter": {
        "name": "OpenRouter (Nemotron 3)",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "models": {
            "nano": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
            "super": "nvidia/nemotron-3-super-120b-a12b:free",
        },
        "headers": {
            "HTTP-Referer": "https://consultor-inmobiliario.app",
            "X-Title": "RyR Consultor Inmobiliario",
        },
    },
    "groq": {
        "name": "Groq (LLaMA 3)",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "models": {
            "nano": "llama-3.1-8b-instant",
            "super": "llama-3.3-70b-versatile",
        },
        "headers": {},
    },
    "gemini": {
        "name": "Gemini (Google)",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "models": {
            "nano": "gemini-2.5-flash",
            "super": "gemini-2.5-flash",
        },
        "headers": {},
    },
}

DEFAULT_PROVIDER = "groq"

# ========== MODELOS (compatibilidad hacia atrás) ==========
MODEL_NANO_OMNI = PROVIDERS[DEFAULT_PROVIDER]["models"]["nano"]
MODEL_SUPER = PROVIDERS[DEFAULT_PROVIDER]["models"]["super"]

# Valor UF aproximado en CLP - se obtiene automaticamente de mindicador.cl
"""Valor UF en CLP - se obtiene automaticamente de mindicador.cl"""
VALOR_UF_FALLBACK = 38000

# Cache simple para evitar llamadas repetidas a la API
_uf_cache = {"value": VALOR_UF_FALLBACK, "timestamp": 0}


def get_active_provider():
    """Retorna el proveedor activo desde session_state o el default."""
    return st.session_state.get("ai_provider", DEFAULT_PROVIDER)


def get_provider_config(provider=None):
    """Retorna la configuración del proveedor."""
    provider = provider or get_active_provider()
    return PROVIDERS.get(provider, PROVIDERS[DEFAULT_PROVIDER])


def get_model_for_provider(tier="super", provider=None):
    """Retorna el modelo según proveedor y tier (nano/super)."""
    config = get_provider_config(provider)
    return config["models"].get(tier, config["models"]["super"])


def _acumular_usage(response):
    """Acumula tokens de una respuesta OpenAI no-streaming en session_state."""
    if hasattr(response, 'usage') and response.usage:
        usage = st.session_state.setdefault("token_usage", {"prompt": 0, "completion": 0, "total": 0})
        usage["prompt"] += response.usage.prompt_tokens or 0
        usage["completion"] += response.usage.completion_tokens or 0
        usage["total"] += response.usage.total_tokens or 0


def _get_api_key(provider=None):
    """Obtiene la API key: st.secrets > variable de entorno."""
    provider = provider or get_active_provider()
    config = get_provider_config(provider)
    env_var = config["api_key_env"]

    return os.getenv(env_var) or st.secrets.get(env_var, "")


def get_ai_client(provider=None):
    """Retorna el cliente de OpenAI configurado para el proveedor elegido."""
    provider = provider or get_active_provider()
    config = get_provider_config(provider)
    api_key = _get_api_key(provider)

    if not api_key or api_key == "tu_api_key_aqui":
        return None

    kwargs = {
        "base_url": config["base_url"],
        "api_key": api_key,
    }
    if config.get("headers"):
        kwargs["default_headers"] = config["headers"]

    return OpenAI(**kwargs)


def get_openai_client():
    """Compatibilidad hacia atrás: usa el proveedor activo."""
    return get_ai_client()


def verificar_api_key(provider=None):
    """Verifica si la API key del proveedor activo está configurada (runtime o .env)."""
    provider = provider or get_active_provider()
    api_key = _get_api_key(provider)
    return bool(api_key) and api_key != "tu_api_key_aqui"


def obtener_valor_uf():
    """Obtiene el valor actual de la UF desde mindicador.cl.
    Cache de 1 hora para no sobrecargar la API.
    Si falla, retorna el valor de respaldo."""
    now = time.time()
    # Cache expira cada 1 hora
    if now - _uf_cache["timestamp"] > 3600:
        try:
            resp = requests.get("https://mindicador.cl/api/uf", timeout=10)
            data = resp.json()
            serie = data.get("serie", [])
            if serie:
                _uf_cache["value"] = serie[0].get("valor", VALOR_UF_FALLBACK)
                _uf_cache["timestamp"] = now
        except Exception:
            pass  # Usar cache anterior o fallback
    return round(_uf_cache["value"], 0)


def calcular_limite_uf(ingresos_totales):
    '''Calcula el máximo de UF que un cliente puede pagar según sus ingresos totales mensuales.
    Fórmula: (ingresos_totales / 625) + 200 = límite UF
    '''
    return (ingresos_totales / 625) + 200


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
        return [{"error": f"Error al buscar: {str(e)}"}]


def extraer_texto_pdf(file_bytes):
    """
    Extrae texto de un archivo PDF.
    Si el PDF tiene poco texto (escaneado/imagen), usa OCR con Tesseract.
    """
    try:
        # Intentar extraer texto con pypdf primero
        from pypdf import PdfReader
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        texto = []
        for i in range(len(reader.pages)):
            page = reader.pages[i]
            page_text = page.extract_text() or ""
            texto.append(page_text)
        resultado = "\n\n".join(texto).strip()

        # Si tiene muy poco texto, probablemente es un PDF escaneado - usar OCR
        if len(resultado) < 50:
            return _ocr_pdf(file_bytes)

        return resultado if resultado else _ocr_pdf(file_bytes)
    except Exception as e:
        # Fallback a OCR si pypdf falla
        try:
            return _ocr_pdf(file_bytes)
        except Exception:
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


def analizar_proyecto_por_nombre(nombre):
    """
    Busca información del proyecto en la web y usa Nemotron 3 Nano Omni
    para generar una descripción detallada.
    Retorna (descripcion, resultados_web).
    """
    query = f"{nombre} capitalizarme.com"
    resultados = buscar_en_web(query)

    if resultados and len(resultados) > 0 and "error" not in resultados[0]:
        contexto = "Información encontrada en la web:\n\n"
        for i, r in enumerate(resultados, 1):
            contexto += f"{i}. {r['titulo']}\n"
            contexto += f"   {r['snippet']}\n\n"
    else:
        contexto = "No se encontró información en la web sobre este proyecto."

    return contexto, resultados


def generar_descripcion_con_ai(nombre, contexto_web="", tier="nano"):
    """
    Usa el proveedor activo para generar una descripción detallada del proyecto.
    """
    client = get_ai_client()
    if not client:
        return None
    model = get_model_for_provider(tier)

    system_prompt = (
        "Eres consultor inmobiliario. Genera una ficha breve del proyecto en español, "
        "máximo 3 párrafos: tipo, ubicación, características, precio UF, público objetivo."
    )

    if contexto_web and "No se encontró" not in contexto_web:
        user_prompt = (
            f"Basado en esta búsqueda web, genera una ficha breve del proyecto \"{nombre}\".\n\n"
            f"{contexto_web}\n\nMáximo 3 párrafos."
        )
    else:
        user_prompt = (
            f"Genera una ficha breve y profesional para el proyecto \"{nombre}\". "
            "Indica que la información es preliminar. Máximo 3 párrafos."
        )

    try:
        response = client.chat.completions.create(
            model=get_model_for_provider(tier),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
        )
        _acumular_usage(response)
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al analizar cotizaciones: {str(e)}"


def generar_recomendacion_inicial(cliente, proyectos, tier="super"):
    """
    Genera la primera recomendación: qué proyecto es más acorde al perfil del cliente.
    """
    client = get_ai_client()
    if not client:
        return None

    datos_cliente = f"""
DATOS DEL CLIENTE:
- Nombre: {cliente.get('nombre', 'N/A')}
- RUT: {cliente.get('rut', 'N/A')}
- Estado Civil: {cliente.get('estado_civil', 'N/A')}
- Profesión: {cliente.get('profesion', 'N/A')}
- Objetivo: {cliente.get('objetivo', 'N/A')}
- Estrategia: {cliente.get('sub_objetivo', 'N/A') if cliente.get('sub_objetivo') else 'N/A'}

INGRESOS:
- Renta: ${cliente.get('ingresos', {}).get('renta', 0):,}
- Dividendos: ${cliente.get('ingresos', {}).get('dividendos', 0):,}
- Pensiones: ${cliente.get('ingresos', {}).get('pensiones', 0):,}
- Arriendos: ${cliente.get('ingresos', {}).get('arriendos', 0):,}

DEUDAS VIGENTES:
"""
    total_descuento_deudas = 0
    for d in cliente.get('deudas', []):
        desc_info = ""
        if d.get('descontar'):
            total_descuento_deudas += d.get('cuota', 0)
            desc_info = " (SE DESCUENTA DE INGRESOS)"
        datos_cliente += f"- {d.get('tipo', 'N/A')} | {d.get('institucion', 'N/A')} | Cuota: ${d.get('cuota', 0):,}{desc_info} | Total: ${d.get('total', 0):,} | {d.get('nro_cuota', 0)} cuotas\n"

    datos_cliente += "\nACTIVOS:\n"
    for a in cliente.get('activos', []):
        nombre_a = a.get('nombre') or a.get('tipo', 'N/A')
        datos_cliente += f"- {nombre_a}: ${a.get('valor', 0):,}\n"

    datos_cliente += "\nCUENTAS:\n"
    for c in cliente.get('cuentas', []):
        banco_c = c.get('banco') or c.get('institucion', 'N/A')
        datos_cliente += f"- {c.get('tipo', 'N/A')} en {banco_c}\n"

    # Calcular límite UF del cliente
    ingresos = cliente.get('ingresos', {})
    total_ingresos_brutos = sum(ingresos.values())
    total_ingresos_para_calculo = max(0, total_ingresos_brutos - total_descuento_deudas)
    limite_uf = calcular_limite_uf(total_ingresos_para_calculo)
    
    datos_cliente += f"\nCAPACIDAD DE INVERSIÓN:\n"
    datos_cliente += f"- Ahorro para pie: ${cliente.get('capacidad_inversion', {}).get('ahorro_pie', 0):,}\n"
    datos_cliente += f"- CAM (Capacidad de Ahorro Mensual): ${cliente.get('capacidad_inversion', {}).get('cam', 0):,}\n"
    datos_cliente += f"\nLÍMITE DE COMPRA (Basado en ingresos disponibles):\n"
    datos_cliente += f"- Ingresos brutos: ${total_ingresos_brutos:,}\n"
    if total_descuento_deudas > 0:
        datos_cliente += f"- Descuento por deudas: -${total_descuento_deudas:,}\n"
    datos_cliente += f"- Ingresos para cálculo: ${total_ingresos_para_calculo:,}\n"
    datos_cliente += f"- Límite máximo en UF: {limite_uf:,.2f} UF\n"
    datos_cliente += f"- Límite máximo en CLP: ${limite_uf * obtener_valor_uf():,.0f}\n\n"

    proyectos_text = "\nPROYECTOS DISPONIBLES:\n\n"
    for p in proyectos:
        precio = p.get('precio_uf', 0)
        etiquetas = p.get('etiquetas', [])
        proyectos_text += f"--- {p['nombre']} ---"
        if etiquetas:
            proyectos_text += f" [🏷️ {', '.join(etiquetas)}]"
        if precio > 0:
            dentro = " ✅ DENTRO DEL PRESUPUESTO" if precio <= limite_uf else " ❌ SOBRE EL PRESUPUESTO"
            proyectos_text += dentro + "\n"
            proyectos_text += f"   Precio: {precio:,.2f} UF (${precio * obtener_valor_uf():,} CLP aprox)\n"
        else:
            proyectos_text += " (Precio no especificado)\n"
            proyectos_text += "   Precio: No especificado\n"
        proyectos_text += f"{p['descripcion'][:1000]}...\n"
        
        cotizaciones = p.get('cotizaciones', {})
        if cotizaciones:
            proyectos_text += "   COTIZACIONES DISPONIBLES:\n"
            for tipo, datos in cotizaciones.items():
                if datos.get('precio', 0) > 0:
                    proyectos_text += f"   - {tipo}: {datos['precio']} UF ({datos.get('detalles', '')})\n"
            if p.get('analisis_cotizaciones'):
                proyectos_text += f"   ANÁLISIS AI COTIZACIONES: {p['analisis_cotizaciones']}\n"
        proyectos_text += "\n"

    # ===== PROMOCIONES ACTIVAS =====
    promociones_activas = get_promociones()
    proyecto_ids = {p_ctx.get("id", "") for p_ctx in proyectos}
    promos_proyecto = [pr for pr in promociones_activas if pr["proyecto_id"] in proyecto_ids]
    if promos_proyecto:
        proyectos_text += "PROMOCIONES ACTIVAS:\n"
        promos_por_mes = defaultdict(list)
        for promo in promos_proyecto:
            promos_por_mes[promo["mes"]].append(promo)
        for mes, promos in sorted(promos_por_mes.items()):
            proyectos_text += f"  [{mes}]\n"
            for promo in promos:
                proyectos_text += f"    - {promo['nombre_proyecto']}: {promo['descripcion_promocion']}\n"
        proyectos_text += "\n"

    system_prompt = (
        "Eres asesor inmobiliario. Responde en español con el siguiente formato:\n\n"
        "**Opción A: [Nombre proyecto]** — [tipología recomendada, ej: 2D2B]\n"
        "- **Por qué:** [razón basada en perfil financiero, etiquetas, y capacidad de pago]\n"
        "- **Precio:** [XX UF - dentro/sobre presupuesto]\n"
        "- **Promociones:** [si aplica, mencionar beneficio]\n"
        "- **Cotizaciones:** [si aplica, detalle por tipología]\n\n"
        "**Opción B: [Nombre proyecto]** — [tipología recomendada]\n"
        "(misma estructura)\n\n"
        "Solo muestra las 3 mejores opciones: Opción A, Opción B y Opción C. "
        "No muestres más de 3 opciones bajo ningún motivo. "
        "Sé concreto y basado en los datos financieros del cliente.\n\n"
        "REGLAS DE PRIORIDAD:\n"
        "1. Los proyectos cuyas etiquetas coincidan con la estrategia de inversión del cliente "
        "(Rentabilidad, Jubilación, Libertad financiera) deben ir PRIMERO.\n"
        "2. Dentro del mismo nivel de coincidencia de etiquetas, prioriza los que estén "
        "dentro del presupuesto del cliente.\n"
        "3. Si ningún proyecto coincide con etiquetas, prioriza por ajuste financiero."
    )

    user_prompt = (
        f"Cliente:\n{datos_cliente}\n\n{proyectos_text}\n"
        "La estrategia de inversión del cliente está indicada en 'Estrategia'. "
        "Prioriza los proyectos cuyas etiquetas coincidan con esa estrategia.\n"
        "Recomiéndame los mejores proyectos en formato punteo "
        "(Opción A, Opción B, etc.) indicando tipología, precio, promociones activas, "
        "cotizaciones disponibles, y el motivo de cada recomendación."
    )

    try:
        response = client.chat.completions.create(
            model=get_model_for_provider(tier),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        _acumular_usage(response)
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al generar recomendación: {str(e)}"


def analizar_excel_promociones(texto_excel, nombre_mes, tier="nano"):
    """
    Usa el proveedor activo para analizar un Excel de promociones.
    texto_excel: contenido extraido del archivo Excel.
    nombre_mes: nombre de la promocion/mes (ej: "Promocion Julio 2026").
    tier: "super" o "nano".
    Retorna una lista de dicts con {nombre_proyecto, promocion}.
    """
    client = get_ai_client()
    if not client:
        return None

    if len(texto_excel) > 25000:
        texto_excel = texto_excel[:25000] + "\n\n[... texto truncado ...]"

    system_prompt = """Eres un experto extractor de datos JSON. Tu única misión es transformar filas de Excel en una lista JSON válida.

DATOS A EXTRAER POR FILA:
1. "nombre_proyecto": El valor de la columna "Proyecto".
2. "promocion": Una síntesis de las columnas "Tipología", "Bono Pie", "UpFront", "A.G", "Otras Promos" y "Reserva a $0".

REGLAS DE ORO:
- Responde EXCLUSIVAMENTE con el bloque JSON.
- No incluyas explicaciones, saludos ni comentarios.
- Si no hay datos, responde [].
- Asegúrate de que el JSON sea válido y no tenga comas sobrantes.

FORMATO REQUERIDO:
[
  {"nombre_proyecto": "Nombre", "promocion": "Tipología: ..., Bono Pie: ..., etc."}
]"""

    user_prompt = f"Convierte los datos de la promoción '{nombre_mes}' a JSON:\n\n{texto_excel}"

    try:
        response = client.chat.completions.create(
            model=get_model_for_provider(tier),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0, # Temperatura 0 para máxima precisión
            max_tokens=3000,
        )
        _acumular_usage(response)
        texto = response.choices[0].message.content.strip()
        
        # --- ESTRATEGIA DE RECUPERACIÓN DE "MAGIA" ---
        import json
        import re

        # 1. Limpieza básica de Markdown
        texto = re.sub(r'```json\s*|```\s*', '', texto).strip()

        # 2. Intento de par más externo [ ]
        match_array = re.search(r'(\[.*\])', texto, re.DOTALL)
        if match_array:
            try:
                return json.loads(match_array.group(1))
            except:
                pass

        # 3. Si falló, intentar limpiar comas finales comunes en LLMs
        if match_array:
            cleaned = re.sub(r',\s*\]', ']', match_array.group(1))
            cleaned = re.sub(r',\s*}', '}', cleaned)
            try:
                return json.loads(cleaned)
            except:
                pass

        # 4. Recuperación quirúrgica: extraer cada { } por separado
        objs = re.findall(r'(\{[^{}]+\})', texto, re.DOTALL)
        if objs:
            recovered_list = []
            for obj_str in objs:
                try:
                    # Intentar limpiar el objeto individual
                    obj_clean = re.sub(r',\s*}', '}', obj_str)
                    recovered_list.append(json.loads(obj_clean))
                except:
                    continue
            if recovered_list:
                return recovered_list
                
        return []
    except Exception as e:
        return []


def chat_stream(mensajes, tier="super"):
    """
    Genera una respuesta en streaming.
    mensajes: lista de dicts con role y content para el historial del chat.
    tier: "super" (LLaMA 3.3 70B) o "nano" (LLaMA 3.1 8B).
    Retorna un generador que emite fragmentos de texto.
    """
    client = get_ai_client()
    if not client:
        yield "⚠️ Error: API Key no configurada. Configúrala en el archivo .env para el proveedor activo."
        return

    system_prompt = {
        "role": "system",
        "content": (
            "Eres asesor inmobiliario. Responde en español, máximo 3 párrafos, "
            "sé breve y directo. Ayuda al cliente según su perfil financiero y proyectos disponibles."
        ),
    }
    messages = [system_prompt] + mensajes

    try:
        response = client.chat.completions.create(
            model=get_model_for_provider(tier),
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            stream=True,
            stream_options={"include_usage": True},
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
            if hasattr(chunk, 'usage') and chunk.usage:
                usage = st.session_state.setdefault("token_usage", {"prompt": 0, "completion": 0, "total": 0})
                usage["prompt"] += chunk.usage.prompt_tokens or 0
                usage["completion"] += chunk.usage.completion_tokens or 0
                usage["total"] += chunk.usage.total_tokens or 0
    except Exception as e:
        yield f"\n\n⚠️ Error: {str(e)}"
