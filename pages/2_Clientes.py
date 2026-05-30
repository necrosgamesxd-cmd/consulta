"""
Página de gestión de clientes con ficha financiera completa.
"""

import streamlit as st
from html import escape
from storage import get_clientes, add_cliente, update_cliente, delete_cliente
from utils import calcular_limite_uf

st.markdown("# 👥 Clientes")
st.markdown("Registra la ficha financiera completa de tus clientes.")


def _generar_ficha_html(cliente):
    """Genera un reporte HTML completo de la ficha financiera del cliente."""
    c = cliente
    ingresos = c.get("ingresos", {})
    total_ingresos_brutos = sum(ingresos.values())
    deudas = c.get("deudas", [])
    total_descuento = sum(d.get("cuota", 0) for d in deudas if d.get("descontar"))
    total_ingresos_netos = max(0, total_ingresos_brutos - total_descuento)
    capacidad = c.get("capacidad_inversion", {})

    def esc(val):
        """Escapa HTML y retorna el valor o 'N/A' si es vacío."""
        return escape(str(val)) if val else 'N/A'

    def fmt(val):
        return f"${val:,.0f}" if val else "$0"

    def si_no(val):
        return "Sí" if val else "No"

    nombre_cliente = esc(c['nombre'])

    deudas_rows = ""
    for d in deudas:
        deudas_rows += f"""<tr>
            <td>{esc(d.get('tipo'))}</td>
            <td>{esc(d.get('institucion'))}</td>
            <td>{fmt(d.get('cuota', 0))}</td>
            <td>{fmt(d.get('total', 0))}</td>
            <td>{d.get('nro_cuota', 0)}</td>
            <td>{si_no(d.get('descontar'))}</td>
        </tr>"""

    activos_rows = ""
    for a in c.get("activos", []):
        nombre_a = esc(a.get('nombre') or a.get('tipo'))
        activos_rows += f"<tr><td>{nombre_a}</td><td>{fmt(a.get('valor', 0))}</td></tr>"

    cuentas_rows = ""
    for ct in c.get("cuentas", []):
        banco_c = esc(ct.get('banco') or ct.get('institucion'))
        cuentas_rows += f"<tr><td>{esc(ct.get('tipo'))}</td><td>{banco_c}</td></tr>"

    fecha = c.get('created_at', '')[:10] if c.get('created_at') else 'N/A'

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ficha Financiera - {c['nombre']}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #121212; font-family: 'Inter', sans-serif; color: #ffffff; padding: 0; min-height: 100vh; }}
  .page {{ max-width: 1100px; margin: 0 auto; padding: 48px 56px; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 48px; }}
  .brand {{ font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 600; color: #D4AF37; letter-spacing: 0.5px; }}
  .brand-sub {{ font-size: 11px; color: #6b7280; letter-spacing: 2px; text-transform: uppercase; margin-top: 4px; }}
  .header-right {{ text-align: right; }}
  .header-right .line {{ font-size: 11px; color: #9ca3af; letter-spacing: 1.5px; text-transform: uppercase; font-weight: 400; }}
  .header-right .line + .line {{ margin-top: 2px; }}
  .divider {{ width: 60px; height: 2px; background: linear-gradient(90deg, #D4AF37, rgba(212,175,55,0.2)); margin-bottom: 28px; }}
  .client-name {{ font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 700; color: #ffffff; line-height: 1.2; margin-bottom: 4px; }}
  .client-sub {{ font-size: 14px; color: #6b7280; font-weight: 300; margin-bottom: 32px; }}
  .highlight {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 40px; }}
  .highlight-item {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(212,175,55,0.12); border-radius: 12px; padding: 20px 24px; text-align: center; }}
  .highlight-item .num {{ font-size: 22px; font-weight: 700; color: #D4AF37; }}
  .highlight-item .lbl {{ font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 6px; }}
  .section {{ margin-bottom: 32px; }}
  .section-title {{ font-family: 'Playfair Display', serif; font-size: 15px; color: #D4AF37; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 16px; }}
  .section-title::after {{ content: ''; display: block; width: 40px; height: 1px; background: rgba(212,175,55,0.3); margin-top: 8px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px 32px; }}
  .grid-2 .label {{ font-size: 11px; color: #6b7280; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }}
  .grid-2 .value {{ font-size: 15px; font-weight: 500; color: #ffffff; margin-top: 2px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ font-size: 11px; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; padding: 10px 14px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); }}
  td {{ padding: 10px 14px; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 14px; color: #d1d5db; }}
  tr:last-child td {{ border-bottom: none; }}
  tr.total td {{ font-weight: 600; color: #ffffff; background: rgba(212,175,55,0.06); }}
  .empty-state {{ font-size: 13px; color: #6b7280; font-style: italic; padding: 12px 0; }}
  .footer {{ margin-top: 48px; padding-top: 24px; border-top: 1px solid rgba(255,255,255,0.06); display: flex; justify-content: space-between; font-size: 11px; color: #4b5563; letter-spacing: 0.5px; }}
  .badge {{ display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 11px; font-weight: 500; letter-spacing: 0.5px; color: #D4AF37; border: 1px solid rgba(212,175,55,0.25); background: rgba(212,175,55,0.06); }}
  @media print {{ body {{ background: #121212; }} }}
  @media (max-width: 768px) {{ .page {{ padding: 24px; }} .highlight {{ grid-template-columns: 1fr; }} .grid-2 {{ grid-template-columns: 1fr; }} .client-name {{ font-size: 26px; }} }}
</style>
</head>
<body>
<div class="page">
  <div class="header">
    <div>
      <div class="brand">RyR Consultor Inmobiliario</div>
      <div class="brand-sub">Ficha Financiera Privada</div>
    </div>
    <div class="header-right">
      <div class="line">División Residencial Premium</div>
      <div class="line">15 Años de Experiencia</div>
    </div>
  </div>

  <div class="divider"></div>

  <div class="client-name">{nombre_cliente}</div>
  <div class="client-sub">Registrado el {fecha} &middot; {esc(c.get('profesion', 'N/A'))}</div>

  <div class="highlight">
    <div class="highlight-item">
      <div class="num">{fmt(total_ingresos_brutos)}</div>
      <div class="lbl">Ingresos Totales / Mes</div>
    </div>
    <div class="highlight-item">
      <div class="num">{fmt(total_ingresos_netos)}</div>
      <div class="lbl">Ingresos Netos / Mes</div>
    </div>
    <div class="highlight-item">
      <div class="num">{calcular_limite_uf(total_ingresos_netos):,.2f}</div>
      <div class="lbl">Límite Máx. Crédito (UF)</div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Datos Personales</div>
    <div class="grid-2">
      <div><div class="label">Nombre</div><div class="value">{nombre_cliente}</div></div>
      <div><div class="label">RUT</div><div class="value">{esc(c.get('rut'))}</div></div>
      <div><div class="label">Teléfono</div><div class="value">{esc(c.get('telefono'))}</div></div>
      <div><div class="label">Correo</div><div class="value">{esc(c.get('correo'))}</div></div>
      <div><div class="label">Estado Civil</div><div class="value">{esc(c.get('estado_civil'))}</div></div>
      <div><div class="label">Profesión</div><div class="value">{esc(c.get('profesion'))}</div></div>
      <div><div class="label">Dirección</div><div class="value">{esc(c.get('direccion'))}</div></div>
      <div><div class="label">Objetivo</div><div class="value">{esc(c.get('objetivo'))}{f" ({esc(c.get('sub_objetivo', ''))})" if c.get('sub_objetivo') else ''}</div></div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Ingresos Mensuales</div>
    <table>
      <tr><th>Fuente</th><th>Monto</th></tr>
      <tr><td>Renta</td><td>{fmt(ingresos.get('renta', 0))}</td></tr>
      <tr><td>Dividendos</td><td>{fmt(ingresos.get('dividendos', 0))}</td></tr>
      <tr><td>Pensiones</td><td>{fmt(ingresos.get('pensiones', 0))}</td></tr>
      <tr><td>Arriendos</td><td>{fmt(ingresos.get('arriendos', 0))}</td></tr>
      <tr class="total"><td>TOTAL</td><td>{fmt(total_ingresos_brutos)}</td></tr>
    </table>
  </div>

  <div class="section">
    <div class="section-title">Capacidad de Inversión</div>
    <div class="grid-2">
      <div><div class="label">Límite Máx. Crédito</div><div class="value"><span class="badge">{calcular_limite_uf(total_ingresos_netos):,.2f} UF</span></div></div>
      <div><div class="label">CAM</div><div class="value">{fmt(capacidad.get('cam', 0))}</div></div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Deudas Vigentes</div>
    {"""<table><tr><th>Tipo</th><th>Institución</th><th>Cuota</th><th>Saldo Total</th><th>Cuotas Rest.</th><th>Descuenta</th></tr>""" + deudas_rows + "</table>" if deudas else '<div class="empty-state">Sin deudas registradas.</div>'}
  </div>

  <div class="section">
    <div class="section-title">Activos</div>
    {"""<table><tr><th>Nombre</th><th>Valor Estimado</th></tr>""" + activos_rows + "</table>" if activos_rows else '<div class="empty-state">Sin activos registrados.</div>'}
  </div>

  <div class="section">
    <div class="section-title">Cuentas Bancarias</div>
    {"""<table><tr><th>Tipo</th><th>Banco / Institución</th></tr>""" + cuentas_rows + "</table>" if cuentas_rows else '<div class="empty-state">Sin cuentas registradas.</div>'}
  </div>

  <div class="footer">
    <span>RyR Consultor Inmobiliario &mdash; Documento Confidencial</span>
    <span>Generado el {fecha}</span>
  </div>
</div>
</body>
</html>"""
    return html

# ===== FORMULARIO NUEVO CLIENTE =====
with st.expander("➕ Registrar nuevo cliente", expanded=False):
    # Eliminamos st.form para evitar que el Enter envíe todo accidentalmente
    st.markdown("### 📋 Datos del Cliente")
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre completo", placeholder="Ej: Juan Pérez", key="new_nombre")
        telefono = st.text_input("Teléfono", placeholder="+56 9 1234 5678", key="new_tel")
        correo = st.text_input("Correo electrónico", placeholder="juan@email.com", key="new_mail")
    with col2:
        rut = st.text_input("RUT", placeholder="12.345.678-9", key="new_rut")
        estado_civil = st.selectbox("Estado Civil", ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a", "Conviviente"], key="new_est")
        profesion = st.text_input("Profesión / Ocupación", placeholder="Ej: Ingeniero Comercial", key="new_prof")
    
    col_obj1, col_obj2 = st.columns(2)
    with col_obj1:
        objetivo = st.selectbox("Objetivo de la compra", ["Vivir", "Invertir"], key="new_obj")
    with col_obj2:
        if objetivo == "Invertir":
            sub_objetivo = st.selectbox("Estrategia de inversión", ["Rentabilidad", "Jubilación", "Libertad financiera"], key="new_sub_obj")
        else:
            sub_objetivo = None
            
    direccion = st.text_input("Dirección", placeholder="Av. Siempre Viva 123, Santiago", key="new_dir")

    st.markdown("---")
    st.markdown("### 💰 Ingresos y Renta")
    col1, col2 = st.columns(2)
    with col1:
        renta = st.number_input("Renta mensual ($)", min_value=0, step=100000, value=0, format="%d", key="new_renta")
        dividendos = st.number_input("Dividendos ($)", min_value=0, step=10000, value=0, format="%d", key="new_div")
    with col2:
        pensiones = st.number_input("Pensiones ($)", min_value=0, step=10000, value=0, format="%d", key="new_pens")
        arriendos = st.number_input("Arriendos ($)", min_value=0, step=10000, value=0, format="%d", key="new_arr")

    st.markdown("---")
    st.markdown("### 🏦 Capacidad de Inversión")
    col1, col2 = st.columns(2)
    with col1:
        ahorro_pie = st.number_input("Ahorro para pie ($)", min_value=0, step=1000000, value=0, format="%d", key="new_pie")
    with col2:
        cam = st.number_input("CAM - Capacidad de Ahorro Mensual ($)", min_value=0, step=1000000, value=0, format="%d", key="new_cam")

    st.markdown("---")
    st.markdown("### 📊 Deudas Vigentes")
    num_deudas = st.number_input("Número de deudas", min_value=0, max_value=10, value=0, step=1, key="num_deudas_input")
    deudas = []
    for i in range(num_deudas):
        st.markdown(f"**Deuda #{i + 1}**")
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        with c1:
            tipo = st.text_input(f"Tipo", key=f"d_tipo_{i}", placeholder="Hipotecario")
        with c2:
            inst = st.text_input(f"Institución", key=f"d_inst_{i}", placeholder="Banco Chile")
        with c3:
            cuota = st.number_input(f"Cuota mensual", key=f"d_cuota_{i}", min_value=0, step=10000, value=0, format="%d")
        with c4:
            descontar = st.checkbox("¿Descontar de ingresos?", key=f"d_desc_{i}")
        
        col_extra1, col_extra2 = st.columns(2)
        with col_extra1:
            total = st.number_input(f"Saldo total deuda", key=f"d_total_{i}", min_value=0, step=100000, value=0, format="%d")
        with col_extra2:
            nro_cuota = st.number_input(f"N° cuotas restantes", key=f"d_nro_{i}", min_value=0, step=1, value=0)
        
        if tipo:
            deudas.append({"tipo": tipo, "institucion": inst, "cuota": cuota, "total": total, "nro_cuota": nro_cuota, "descontar": descontar})

    st.markdown("---")
    st.markdown("### 🏠 Activos")
    num_activos = st.number_input("Número de activos", min_value=0, max_value=10, value=0, step=1, key="num_act_input")
    activos = []
    for i in range(num_activos):
        st.markdown(f"**Activo #{i + 1}**")
        c1, c2 = st.columns([2, 1])
        with c1:
            nombre_a = st.text_input(f"Nombre del activo", key=f"a_nombre_{i}", placeholder="Ej: Depto en Viña")
        with c2:
            valor_a = st.number_input(f"Valor estimado", key=f"a_valor_{i}", min_value=0, step=1000000, value=0, format="%d")
        if nombre_a:
            activos.append({"nombre": nombre_a, "valor": valor_a})

    st.markdown("---")
    st.markdown("### 🏛️ Cuentas Bancarias")
    num_cuentas = st.number_input("Número de cuentas", min_value=0, max_value=10, value=0, step=1, key="num_cta_input")
    cuentas = []
    for i in range(num_cuentas):
        st.markdown(f"**Cuenta #{i + 1}**")
        c1, c2 = st.columns(2)
        with c1:
            tipo_c = st.text_input(f"Tipo de cuenta", key=f"c_tipo_{i}", placeholder="Corriente")
        with c2:
            banco_c = st.text_input(f"Banco / Institución", key=f"c_banco_{i}", placeholder="Santander")
        if tipo_c:
            cuentas.append({"tipo": tipo_c, "banco": banco_c})

    st.markdown("---")
    # Botón normal de Streamlit, NO de formulario
    guardar = st.button("💾 Guardar Cliente", type="primary", use_container_width=True)

    if guardar:
        if nombre:
            data = {
                "nombre": nombre,
                "telefono": telefono,
                "correo": correo,
                "rut": rut,
                "estado_civil": estado_civil,
                "profesion": profesion,
                "objetivo": objetivo,
                "sub_objetivo": sub_objetivo,
                "direccion": direccion,
                "ingresos": {
                    "renta": renta,
                    "dividendos": dividendos,
                    "pensiones": pensiones,
                    "arriendos": arriendos,
                },
                "capacidad_inversion": {
                    "ahorro_pie": ahorro_pie,
                    "cam": cam,
                },
                "deudas": deudas,
                "activos": activos,
                "cuentas": cuentas,
            }
            add_cliente(data)
            st.success(f"✅ Cliente **{nombre}** registrado correctamente")
            # Forzamos un rerun para limpiar los campos (Streamlit recreará los widgets con sus valores por defecto)
            st.rerun()
        else:
            st.error("⚠️ El nombre del cliente es obligatorio")

# ===== LISTA DE CLIENTES =====
st.markdown("---")
st.markdown("## Clientes registrados")

clientes = get_clientes()

if not clientes:
    st.info("📭 No hay clientes registrados. Usa el formulario de arriba para agregar el primero.")
else:
    for c in clientes:
        with st.container():
            cols = st.columns([1, 4, 2, 1, 1, 1])
            with cols[0]:
                st.markdown(f"<h2 style='text-align:center'>👤</h2>", unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"### {c['nombre']}")
                obj_str = f"🎯 {c.get('objetivo', 'N/A')}"
                if c.get('sub_objetivo'):
                    obj_str += f" ({c['sub_objetivo']})"
                st.caption(f"📅 {c['created_at'][:10]} • {c.get('profesion', 'N/A')} • {obj_str}")
            with cols[2]:
                ingresos = c.get("ingresos", {})
                total_ingresos_brutos = sum(ingresos.values())
                deudas = c.get("deudas", [])
                total_descuento = sum(d.get("cuota", 0) for d in deudas if d.get("descontar"))
                total_ingresos_netos = max(0, total_ingresos_brutos - total_descuento)
                
                capacidad = c.get("capacidad_inversion", {})
                st.markdown(f"💰 Ingresos: **${total_ingresos_brutos:,}**")
                if total_descuento > 0:
                    st.caption(f"📉 Neto: ${total_ingresos_netos:,}")
                st.markdown(f"🏦 Pie: **${capacidad.get('ahorro_pie', 0):,}**")
            with cols[3]:
                html_ficha = _generar_ficha_html(c)
                st.download_button(
                    label="📄",
                    data=html_ficha,
                    file_name=f"ficha_{c['nombre'].replace(' ', '_')}.html",
                    mime="text/html",
                    key=f"dl_{c['id']}",
                    help="Descargar ficha financiera completa",
                )
            with cols[4]:
                if st.button("✏️", key=f"edit_{c['id']}", help="Editar cliente"):
                    st.session_state[f"editando_cliente_{c['id']}"] = True
                    st.rerun()
            with cols[5]:
                if st.button("🗑️", key=f"del_{c['id']}", help="Eliminar cliente"):
                    delete_cliente(c["id"])
                    st.rerun()

            # ===== FORMULARIO DE EDICIÓN =====
            if st.session_state.get(f"editando_cliente_{c['id']}", False):
                with st.container(border=True):
                    st.markdown(f"#### ✏️ Editando: {c['nombre']}")
                    cap = c.get("capacidad_inversion", {})
                    ing = c.get("ingresos", {})

                    edit_nombre = st.text_input("Nombre", value=c.get("nombre", ""), key=f"e_nombre_{c['id']}")
                    edit_telefono = st.text_input("Teléfono", value=c.get("telefono", ""), key=f"e_tel_{c['id']}")
                    edit_correo = st.text_input("Correo", value=c.get("correo", ""), key=f"e_mail_{c['id']}")
                    edit_rut = st.text_input("RUT", value=c.get("rut", ""), key=f"e_rut_{c['id']}")
                    edit_profesion = st.text_input("Profesión", value=c.get("profesion", ""), key=f"e_prof_{c['id']}")
                    edit_objetivo = st.selectbox("Objetivo", ["Vivir", "Invertir"], index=0 if c.get("objetivo") == "Vivir" else 1, key=f"e_obj_{c['id']}")
                    edit_direccion = st.text_input("Dirección", value=c.get("direccion", ""), key=f"e_dir_{c['id']}")

                    st.markdown("**💰 Ingresos**")
                    col_i1, col_i2 = st.columns(2)
                    with col_i1:
                        edit_renta = st.number_input("Renta", value=ing.get("renta", 0), key=f"e_renta_{c['id']}")
                        edit_dividendos = st.number_input("Dividendos", value=ing.get("dividendos", 0), key=f"e_div_{c['id']}")
                    with col_i2:
                        edit_pensiones = st.number_input("Pensiones", value=ing.get("pensiones", 0), key=f"e_pens_{c['id']}")
                        edit_arriendos = st.number_input("Arriendos", value=ing.get("arriendos", 0), key=f"e_arr_{c['id']}")

                    st.markdown("**🏦 Capacidad de Inversión**")
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        edit_ahorro_pie = st.number_input("Ahorro para pie ($)", value=cap.get("ahorro_pie", 0), key=f"e_pie_{c['id']}")
                    with col_c2:
                        edit_cam = st.number_input("CAM ($)", value=cap.get("cam", 0), key=f"e_cam_{c['id']}")

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("💾 Guardar cambios", type="primary", key=f"save_cliente_{c['id']}", use_container_width=True):
                            update_cliente(c["id"], **{
                                "nombre": edit_nombre,
                                "telefono": edit_telefono,
                                "correo": edit_correo,
                                "rut": edit_rut,
                                "profesion": edit_profesion,
                                "objetivo": edit_objetivo,
                                "direccion": edit_direccion,
                                "ingresos": {
                                    "renta": edit_renta,
                                    "dividendos": edit_dividendos,
                                    "pensiones": edit_pensiones,
                                    "arriendos": edit_arriendos,
                                },
                                "capacidad_inversion": {
                                    "ahorro_pie": edit_ahorro_pie,
                                    "cam": edit_cam,
                                },
                            })
                            st.session_state[f"editando_cliente_{c['id']}"] = False
                            st.success("✅ Cliente actualizado")
                            st.rerun()
                    with col_btn2:
                        if st.button("❌ Cancelar", key=f"cancel_cliente_{c['id']}", use_container_width=True):
                            st.session_state[f"editando_cliente_{c['id']}"] = False
                            st.rerun()

            with st.expander("📋 Ver ficha financiera completa"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 📋 Datos Personales")
                    st.markdown(f"**Teléfono:** {c.get('telefono', 'N/A')}")
                    st.markdown(f"**Correo:** {c.get('correo', 'N/A')}")
                    st.markdown(f"**RUT:** {c.get('rut', 'N/A')}")
                    st.markdown(f"**Estado Civil:** {c.get('estado_civil', 'N/A')}")
                    st.markdown(f"**Objetivo:** {c.get('objetivo', 'N/A')}")
                    if c.get('sub_objetivo'):
                        st.markdown(f"**Estrategia:** {c.get('sub_objetivo', 'N/A')}")
                    st.markdown(f"**Dirección:** {c.get('direccion', 'N/A')}")

                    st.markdown("#### 💰 Ingresos")
                    st.markdown(f"- Renta: ${ingresos.get('renta', 0):,}")
                    st.markdown(f"- Dividendos: ${ingresos.get('dividendos', 0):,}")
                    st.markdown(f"- Pensiones: ${ingresos.get('pensiones', 0):,}")
                    st.markdown(f"- Arriendos: ${ingresos.get('arriendos', 0):,}")
                    st.markdown(f"**Total: ${total_ingresos_brutos:,}**")

                with col2:
                    st.markdown("#### 🏦 Capacidad de Inversión")
                    capacidad = c.get("capacidad_inversion", {})
                    st.markdown(f"- Ahorro para pie: **${capacidad.get('ahorro_pie', 0):,}**")
                    st.markdown(f"- CAM (Crédito Máx): **${capacidad.get('cam', 0):,}**")

                    deudas = c.get("deudas", [])
                    if deudas:
                        st.markdown("#### 📊 Deudas Vigentes")
                        for d in deudas:
                            desc_str = " (⚠️ Se resta de ingresos)" if d.get('descontar') else ""
                            st.markdown(f"- {d.get('tipo', 'N/A')} en {d.get('institucion', 'N/A')}: ${d.get('cuota', 0):,}/mes{desc_str}")
                            st.caption(f"  Saldo: ${d.get('total', 0):,} | {d.get('nro_cuota', 0)} cuotas rest.")

                    activos = c.get("activos", [])
                    if activos:
                        st.markdown("#### 🏠 Activos")
                        for a in activos:
                            # Soportar nombre antiguo (tipo) y nuevo (nombre)
                            nombre_a = a.get('nombre') or a.get('tipo', 'N/A')
                            st.markdown(f"- {nombre_a}: ${a.get('valor', 0):,}")

                    cuentas = c.get("cuentas", [])
                    if cuentas:
                        st.markdown("#### 🏛️ Cuentas")
                        for ct in cuentas:
                            # Soportar institucion antiguo y banco nuevo
                            banco_c = ct.get('banco') or ct.get('institucion', 'N/A')
                            st.markdown(f"- {ct.get('tipo', 'N/A')} en {banco_c}")

        st.markdown("---")
