"""
Página de gestión de clientes con ficha financiera completa.
"""

import streamlit as st
from storage import get_clientes, add_cliente, delete_cliente

st.markdown("# 👥 Clientes")
st.markdown("Registra la ficha financiera completa de tus clientes.")

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
        cam = st.number_input("CAM - Crédito Aprobado Máximo ($)", min_value=0, step=1000000, value=0, format="%d", key="new_cam")

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
            cols = st.columns([1, 4, 2, 1])
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
                if st.button("🗑️", key=f"del_{c['id']}", help="Eliminar cliente"):
                    delete_cliente(c["id"])
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
