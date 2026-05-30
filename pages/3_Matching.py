"""
Página de matching: chat con AI para recomendar proyectos a clientes.
"""

from datetime import datetime

import streamlit as st
from storage import get_clientes, get_proyectos, get_promociones
from utils import generar_recomendacion_inicial, chat_stream, verificar_api_key, obtener_valor_uf, calcular_limite_uf

st.markdown("# 💬 Matching Inteligente")
st.markdown("Selecciona un cliente y el AI te recomendará el proyecto más adecuado para su perfil.")

api_ok = verificar_api_key()

if not api_ok:
    st.error("⚠️ Configura tu API Key en el archivo .env para el proveedor seleccionado.")
    st.stop()

clientes = get_clientes()
proyectos = get_proyectos()

if not clientes:
    st.warning("👥 No hay clientes registrados. Ve a la sección **Clientes** para agregar uno.")
    st.stop()

if not proyectos:
    st.warning("📋 No hay proyectos registrados. Ve a la sección **Proyectos** para agregar uno.")
    st.stop()

# ===== SELECCIÓN DE MODELO =====
st.markdown("### ⚙️ Modelo de IA")
col_m1, col_m2 = st.columns([1, 3])
with col_m1:
    tier = st.radio(
        "Modelo",
        options=["super", "nano"],
        format_func=lambda x: "Super (LLaMA 3.3 70B)" if x == "super" else "Nano (LLaMA 3.1 8B)",
        index=0 if st.session_state.get("matching_tier", "super") == "super" else 1,
        key="matching_tier",
        horizontal=True,
        help="Super: mayor calidad, más lento, más tokens. Nano: más rápido, menos tokens, calidad moderada.",
    )

# ===== SELECCIÓN DE CLIENTE =====
st.markdown("### 1. Selecciona un cliente")
cliente_options = {f"{c['nombre']} - {c.get('profesion', 'N/A')}": c for c in clientes}
selected_label = st.selectbox(
    "Cliente",
    options=list(cliente_options.keys()),
    index=0,
    label_visibility="collapsed",
)
cliente = cliente_options[selected_label]

# ===== MOSTRAR INFO RÁPIDA DEL CLIENTE =====
with st.expander("📋 Ver resumen del cliente", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        ingresos = cliente.get("ingresos", {})
        total_ingresos = sum(ingresos.values())
        st.markdown(f"**{cliente['nombre']}**")
        st.markdown(f"📧 {cliente.get('correo', 'N/A')} | 📞 {cliente.get('telefono', 'N/A')}")
        obj_text = f"🎯 {cliente.get('objetivo', 'N/A')}"
        if cliente.get('sub_objetivo'):
            obj_text += f" ({cliente['sub_objetivo']})"
        st.markdown(f"**Objetivo:** {obj_text}")
        st.markdown(f"**Ingresos totales:** ${total_ingresos:,}/mes")
    with col2:
        capacidad = cliente.get("capacidad_inversion", {})
        st.markdown(f"**Ahorro para pie:** ${capacidad.get('ahorro_pie', 0):,}")
        st.markdown(f"**CAM:** ${capacidad.get('cam', 0):,}")
        st.markdown(f"**Deudas activas:** {len(cliente.get('deudas', []))}")

# ===== LÍMITE UF DEL CLIENTE =====
ingresos_cliente = cliente.get("ingresos", {})
total_ingresos_brutos = sum(ingresos_cliente.values())
deudas_cliente = cliente.get("deudas", [])
total_descuento = sum(d.get("cuota", 0) for d in deudas_cliente if d.get("descontar"))
total_ingresos_para_calculo = max(0, total_ingresos_brutos - total_descuento)
limite_uf_cliente = calcular_limite_uf(total_ingresos_para_calculo)

with st.expander("💰 Capacidad de compra", expanded=True):
    col_cap1, col_cap2 = st.columns(2)
    with col_cap1:
        st.markdown(f"**Ingresos brutos:** ${total_ingresos_brutos:,}/mes")
        if total_descuento > 0:
            st.markdown(f"**Descuento deudas:** -${total_descuento:,}/mes")
        st.markdown(f"**Ingresos para cálculo:** ${total_ingresos_para_calculo:,}/mes")
    with col_cap2:
        st.markdown(f"**Límite máximo:** {limite_uf_cliente:,.2f} UF")
        st.markdown(f"**Valor en CLP:** ≈ ${limite_uf_cliente * obtener_valor_uf():,.0f}")

    st.markdown(f"**Fórmula:** ({total_ingresos_para_calculo:,} / 625) + 200 = {limite_uf_cliente:,.2f} UF")
    
    st.markdown("---")
    st.markdown("**Proyectos según tu presupuesto:**")
    dentro_presupuesto = []
    fuera_presupuesto = []
    sin_precio = []
    for p in proyectos:
        precio = p.get("precio_uf", 0)
        if precio > 0:
            if precio <= limite_uf_cliente:
                dentro_presupuesto.append(p)
            else:
                fuera_presupuesto.append(p)
        else:
            sin_precio.append(p)
    
    if dentro_presupuesto:
        st.markdown(f"✅ **{len(dentro_presupuesto)} proyecto(s) dentro de tu presupuesto:**")
        for p in dentro_presupuesto:
            precio = p.get("precio_uf", 0)
            st.markdown(f"- {p['nombre']}: {precio:,.2f} UF")
    
    if fuera_presupuesto:
        st.markdown(f"❌ **{len(fuera_presupuesto)} proyecto(s) sobre tu presupuesto:**")
        for p in fuera_presupuesto:
            precio = p.get("precio_uf", 0)
            st.markdown(f"- {p['nombre']}: {precio:,.2f} UF")
    
    if sin_precio:
        st.markdown(f"⚠️ **{len(sin_precio)} proyecto(s) sin precio definido:**")
        for p in sin_precio:
            st.markdown(f"- {p['nombre']}")

st.markdown("### 2. Chat con Asesor AI")
st.caption("El AI analizará el perfil del cliente y los proyectos disponibles para hacer una recomendación.")

# ===== INICIALIZAR CHAT =====
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "cliente_actual" not in st.session_state:
    st.session_state.cliente_actual = None
if "recomendacion_hecha" not in st.session_state:
    st.session_state.recomendacion_hecha = False

# Si cambia de cliente, reiniciar chat
if st.session_state.cliente_actual != cliente["id"]:
    st.session_state.chat_messages = []
    st.session_state.cliente_actual = cliente["id"]
    st.session_state.recomendacion_hecha = False

# Botón para nuevo análisis
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Nuevo análisis", use_container_width=True):
        st.session_state.chat_messages = []
        st.session_state.recomendacion_hecha = False
        st.rerun()

# Mostrar historial del chat
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ===== FUNCIÓN AUX: construir contexto completo del cliente =====
def _build_full_context(cliente, proyectos):
    """Construye un contexto detallado del cliente y proyectos para el AI."""
    ingresos = cliente.get("ingresos", {})
    capacidad = cliente.get("capacidad_inversion", {})

    ctx = f"""DATOS DEL CLIENTE:
- Nombre: {cliente.get('nombre', 'N/A')}
- RUT: {cliente.get('rut', 'N/A')}
- Estado Civil: {cliente.get('estado_civil', 'N/A')}
- Profesión: {cliente.get('profesion', 'N/A')}
- Dirección: {cliente.get('direccion', 'N/A')}
- Teléfono: {cliente.get('telefono', 'N/A')}
- Email: {cliente.get('correo', 'N/A')}

INGRESOS Y RENTA:
- Renta mensual: ${ingresos.get('renta', 0):,}
- Dividendos: ${ingresos.get('dividendos', 0):,}
- Pensiones: ${ingresos.get('pensiones', 0):,}
- Arriendos: ${ingresos.get('arriendos', 0):,}
- Total ingresos brutos: ${sum(ingresos.values()):,}/mes

CAPACIDAD DE INVERSIÓN:
- Ahorro para pie: ${capacidad.get('ahorro_pie', 0):,}
- CAM (Crédito Máx Aprobado): ${capacidad.get('cam', 0):,}

"""

    deudas = cliente.get("deudas", [])
    total_descuento_ctx = 0
    if deudas:
        ctx += "DEUDAS VIGENTES:\n"
        for d in deudas:
            desc_info = ""
            if d.get('descontar'):
                total_descuento_ctx += d.get('cuota', 0)
                desc_info = " (SE RESTA DE INGRESOS)"
            ctx += f"- {d.get('tipo', 'N/A')} | {d.get('institucion', 'N/A')} | Cuota: ${d.get('cuota', 0):,}/mes{desc_info} | Total: ${d.get('total', 0):,} | {d.get('nro_cuota', 0)} cuotas\n"
        ctx += f"- **Total cuotas mensuales:** ${sum(d.get('cuota', 0) for d in deudas):,}\n"
        ctx += f"- **Total a descontar de ingresos:** ${total_descuento_ctx:,}\n"
        ctx += f"- **Ratio deuda/ingreso:** {sum(d.get('cuota', 0) for d in deudas) / max(sum(ingresos.values()), 1) * 100:.1f}%\n"
        ctx += "\n"

    activos = cliente.get("activos", [])
    if activos:
        ctx += "ACTIVOS:\n"
        for a in activos:
            nombre_a = a.get('nombre') or a.get('tipo', 'N/A')
            ctx += f"- {nombre_a}: ${a.get('valor', 0):,}\n"
        ctx += f"- **Total activos:** ${sum(a.get('valor', 0) for a in activos):,}\n\n"

    cuentas = cliente.get("cuentas", [])
    if cuentas:
        ctx += "CUENTAS BANCARIAS:\n"
        for c in cuentas:
            banco_c = c.get('banco') or c.get('institucion', 'N/A')
            ctx += f"- {c.get('tipo', 'N/A')} en {banco_c}\n"
        ctx += "\n"

    # Calcular límite UF del cliente
    total_ingresos_para_calc = max(0, sum(ingresos.values()) - total_descuento_ctx)
    limite_uf_ctx = calcular_limite_uf(total_ingresos_para_calc)
    ctx += f"LÍMITE DE COMPRA DEL CLIENTE:\n"
    ctx += f"- Ingresos brutos: ${sum(ingresos.values()):,}/mes\n"
    ctx += f"- Ingresos para cálculo (neto de deudas marcadas): ${total_ingresos_para_calc:,}/mes\n"
    ctx += f"- Límite máximo: {limite_uf_ctx:,.2f} UF (~${limite_uf_ctx * obtener_valor_uf():,.0f} CLP)\n"
    ctx += f"- Fórmula: (ingresos_netos / 625) + 200\n\n"

    ctx += "PROYECTOS DISPONIBLES:\n\n"
    for p in proyectos:
        precio_uf = p.get("precio_uf", 0)
        etiquetas_ctx = p.get("etiquetas", [])
        ctx += f"--- {p['nombre']} (Fuente: {p['fuente']}) ---"
        if etiquetas_ctx:
            ctx += f" [🏷️ {', '.join(etiquetas_ctx)}]"
        if precio_uf > 0:
            if precio_uf <= limite_uf_ctx:
                ctx += " ✅ DENTRO DEL PRESUPUESTO"
            else:
                ctx += " ❌ SOBRE EL PRESUPUESTO"
            ctx += f"\n"
            ctx += f"Precio: {precio_uf:,.2f} UF (~${precio_uf * obtener_valor_uf():,} CLP aprox)\n"
        else:
            ctx += " (Precio no especificado)\n"
        ctx += f"{p['descripcion'][:2000]}\n"
        
        cotizaciones_ctx = p.get('cotizaciones', {})
        if cotizaciones_ctx:
            ctx += "  COTIZACIONES:\n"
            for tipo, datos in cotizaciones_ctx.items():
                if datos.get('precio', 0) > 0:
                    ctx += f"    - {tipo}: {datos['precio']} UF | {datos.get('detalles', '')}\n"
            if p.get('analisis_cotizaciones'):
                ctx += f"  ANÁLISIS INVERSIÓN: {p['analisis_cotizaciones']}\n"
        ctx += "\n"


    # ===== PROMOCIONES ACTIVAS =====
    promociones_activas = get_promociones()
    # Obtener IDs de todos los proyectos disponibles
    proyecto_ids = {p_ctx.get("id", "") for p_ctx in proyectos}
    promos_proyecto = [p for p in promociones_activas if p["proyecto_id"] in proyecto_ids]

    if promos_proyecto:
        ctx += "PROMOCIONES ACTIVAS:\n"
        # Agrupar por mes
        from collections import defaultdict
        promos_por_mes = defaultdict(list)
        for promo in promos_proyecto:
            promos_por_mes[promo["mes"]].append(promo)
        
        for mes, promos in sorted(promos_por_mes.items()):
            ctx += f"  [{mes}]\n"
            for promo in promos:
                ctx += f"    - {promo['nombre_proyecto']}: {promo['descripcion_promocion']}\n"
        ctx += "\n"

    return ctx


# Botón para iniciar matching (solo si no hay mensajes)
if not st.session_state.chat_messages:
    st.markdown("### 3. Obtener recomendación")
    if st.button("💬 Recomendar proyecto", type="primary", use_container_width=True):
        with st.chat_message("assistant"):
            with st.spinner("🤔 Analizando perfil del cliente y proyectos disponibles..."):
                tier = st.session_state.get("matching_tier", "super")
                recomendacion = generar_recomendacion_inicial(cliente, proyectos, tier=tier)
            if recomendacion:
                st.markdown(recomendacion)
                st.session_state.chat_messages.append({"role": "assistant", "content": recomendacion})
                st.session_state.recomendacion_hecha = True
            else:
                st.error("Error al generar recomendación. Verifica tu conexión con el proveedor AI.")
                st.stop()
        st.rerun()

# Chat interactivo (solo visible tras la recomendación)
prompt = st.chat_input("Haz una pregunta sobre el proyecto recomendado...") if st.session_state.chat_messages else None
if prompt:
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("💭 Pensando..."):
            # Construir contexto completo del cliente (igual que en la recomendación inicial)
            contexto_completo = _build_full_context(cliente, proyectos)

            context_msg = {
                "role": "system",
                "content": f"Contexto completo del cliente y proyectos:\n\n{contexto_completo}\n\nResponde en español, sé profesional y detallado."
            }

            messages_for_api = [context_msg]
            for m in st.session_state.chat_messages:
                # Saltar el mensaje system de la recomendación inicial si existe
                if m["role"] == "assistant":
                    messages_for_api.append({"role": m["role"], "content": m["content"]})
                elif m["role"] == "user":
                    messages_for_api.append({"role": m["role"], "content": m["content"]})

            tier = st.session_state.get("matching_tier", "super")
            response_text = ""
            response_placeholder = st.empty()
            try:
                for chunk in chat_stream(messages_for_api, tier=tier):
                    response_text += chunk
                    response_placeholder.markdown(response_text + "▌")
            except Exception as e:
                response_text = f"⚠️ Error: {str(e)}"
            response_placeholder.markdown(response_text)

        st.session_state.chat_messages.append({"role": "assistant", "content": response_text})

# ===== EXPORTAR INFORME =====
if st.session_state.chat_messages:
    st.markdown("---")
    st.markdown("### 📄 Exportar informe")

    from html import escape

    c = cliente
    ingresos = c.get("ingresos", {})
    capacidad = c.get("capacidad_inversion", {})
    total_ingresos = sum(ingresos.values())
    deudas_cliente = c.get("deudas", [])
    total_descuento = sum(d.get("cuota", 0) for d in deudas_cliente if d.get("descontar"))
    limite_uf = calcular_limite_uf(max(0, total_ingresos - total_descuento))

    def esc(val):
        return escape(str(val)) if val else 'N/A'

    def fmt(val):
        return f"${val:,.0f}" if val else "$0"

    nombre_cliente = esc(c.get('nombre', 'N/A'))
    fecha = datetime.now().strftime('%Y-%m-%d %H:%M')

    chat_html = ""
    for msg in st.session_state.chat_messages:
        role_label = "Asesor AI" if msg["role"] == "assistant" else "Cliente"
        role_color = "#0f3460" if msg["role"] == "assistant" else "#6b7280"
        bg_color = "#f0f7ff" if msg["role"] == "assistant" else "#f9fafb"
        chat_html += f"""<div class="msg" style="background:{bg_color};">
            <div class="msg-role" style="color:{role_color};">{role_label}</div>
            <div class="msg-content">{esc(msg['content'])}</div>
        </div>"""

    estrategia_html = ""
    if c.get('sub_objetivo'):
        estrategia_html = f"""<div class="grid-item">
            <div class="label">Estrategia</div>
            <div class="value">{esc(c['sub_objetivo'])}</div>
        </div>"""

    descuento_html = ""
    if total_descuento > 0:
        descuento_html = f"""<div class="grid-item">
            <div class="label">Descuento deudas</div>
            <div class="value">-${total_descuento:,}/mes</div>
        </div>"""

    export_text = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Informe de Matching - {c['nombre']}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #121212; font-family: 'Inter', sans-serif; color: #ffffff; padding: 0; min-height: 100vh; }}
  .page {{ max-width: 1000px; margin: 0 auto; padding: 48px 56px; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 48px; }}
  .brand {{ font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 600; color: #D4AF37; letter-spacing: 0.5px; }}
  .brand-sub {{ font-size: 11px; color: #6b7280; letter-spacing: 2px; text-transform: uppercase; margin-top: 4px; }}
  .header-right {{ text-align: right; }}
  .header-right .line {{ font-size: 11px; color: #9ca3af; letter-spacing: 1.5px; text-transform: uppercase; font-weight: 400; }}
  .header-right .line + .line {{ margin-top: 2px; }}
  .divider {{ width: 60px; height: 2px; background: linear-gradient(90deg, #D4AF37, rgba(212,175,55,0.2)); margin-bottom: 28px; }}
  .title {{ font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 700; color: #ffffff; line-height: 1.2; margin-bottom: 4px; }}
  .subtitle {{ font-size: 14px; color: #6b7280; font-weight: 300; margin-bottom: 32px; }}
  .section {{ margin-bottom: 32px; }}
  .section-title {{ font-family: 'Playfair Display', serif; font-size: 15px; color: #D4AF37; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 16px; }}
  .section-title::after {{ content: ''; display: block; width: 40px; height: 1px; background: rgba(212,175,55,0.3); margin-top: 8px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px 32px; }}
  .grid-item .label {{ font-size: 11px; color: #6b7280; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }}
  .grid-item .value {{ font-size: 15px; font-weight: 500; color: #ffffff; margin-top: 2px; }}
  .highlight {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 28px; }}
  .highlight-item {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(212,175,55,0.12); border-radius: 12px; padding: 20px 24px; text-align: center; }}
  .highlight-item .num {{ font-size: 22px; font-weight: 700; color: #D4AF37; }}
  .highlight-item .lbl {{ font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 6px; }}
  .msg {{ padding: 16px; border-radius: 12px; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.06); }}
  .msg-role {{ font-size: 12px; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.5px; }}
  .msg-content {{ font-size: 14px; line-height: 1.7; color: #d1d5db; white-space: pre-wrap; }}
  .limite-box {{ background: rgba(212,175,55,0.06); border: 1px solid rgba(212,175,55,0.2); border-radius: 12px; padding: 20px 24px; text-align: center; }}
  .limite-box .num {{ font-size: 28px; font-weight: 700; color: #D4AF37; }}
  .limite-box .lbl {{ font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; }}
  .footer {{ margin-top: 48px; padding-top: 24px; border-top: 1px solid rgba(255,255,255,0.06); display: flex; justify-content: space-between; font-size: 11px; color: #4b5563; letter-spacing: 0.5px; }}
  @media print {{ body {{ background: #121212; }} }}
  @media (max-width: 768px) {{ .page {{ padding: 24px; }} .highlight {{ grid-template-columns: 1fr; }} .grid-2 {{ grid-template-columns: 1fr; }} .title {{ font-size: 26px; }} }}
</style>
</head>
<body>
<div class="page">
  <div class="header">
    <div>
      <div class="brand">RyR Consultor Inmobiliario</div>
      <div class="brand-sub">Informe de Matching Privado</div>
    </div>
    <div class="header-right">
      <div class="line">División Residencial Premium</div>
      <div class="line">15 Años de Experiencia</div>
    </div>
  </div>

  <div class="divider"></div>

  <div class="title">Informe de Matching</div>
  <div class="subtitle">{nombre_cliente} &middot; {fecha}</div>

  <div class="section">
    <div class="section-title">Perfil Financiero del Cliente</div>
    <div class="grid-2">
      <div class="grid-item"><div class="label">Nombre</div><div class="value">{nombre_cliente}</div></div>
      <div class="grid-item"><div class="label">RUT</div><div class="value">{esc(c.get('rut'))}</div></div>
      <div class="grid-item"><div class="label">Profesión</div><div class="value">{esc(c.get('profesion'))}</div></div>
      <div class="grid-item"><div class="label">Objetivo</div><div class="value">{esc(c.get('objetivo'))}</div></div>
      {estrategia_html}
    </div>
  </div>

  <div class="highlight">
    <div class="highlight-item">
      <div class="num">{fmt(total_ingresos)}</div>
      <div class="lbl">Ingresos / Mes</div>
    </div>
    <div class="highlight-item">
      <div class="num">{fmt(capacidad.get('ahorro_pie', 0))}</div>
      <div class="lbl">Ahorro para Pie</div>
    </div>
    <div class="highlight-item">
      <div class="num">{fmt(capacidad.get('cam', 0))}</div>
      <div class="lbl">CAM</div>
    </div>
  </div>
  {descuento_html}
  <div class="section">
    <div class="section-title">Límite de Compra</div>
    <div class="limite-box">
      <div class="num">{limite_uf:,.2f} UF</div>
      <div class="lbl">Máximo Disponible</div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Conversación</div>
    {chat_html}
  </div>

  <div class="footer">
    <span>RyR Consultor Inmobiliario &mdash; Documento Confidencial</span>
    <span>Generado el {fecha}</span>
  </div>
</div>
</body>
</html>"""

    st.download_button(
        "📥 Descargar informe (.html)",
        data=export_text,
        file_name=f"matching_{cliente['nombre'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
        mime="text/html",
        use_container_width=True,
    )
