"""
Página de gestión de proyectos inmobiliarios.
"""

import streamlit as st
from storage import get_proyectos, add_proyecto, delete_proyecto, update_proyecto
from utils import (
    analizar_proyecto_por_nombre,
    generar_descripcion_con_ai,
    extraer_texto_pdf,
    analizar_pdf_con_ai,
    verificar_api_key,
    analizar_cotizacion_con_ai
)

st.markdown("# 📋 Proyectos Inmobiliarios")
st.markdown("Agrega y gestiona los proyectos que quieres ofrecer a tus clientes.")

api_ok = verificar_api_key()

# ===== FORMULARIO PARA NUEVO PROYECTO =====
with st.expander("➕ Agregar nuevo proyecto", expanded=False):
    tab1, tab2 = st.tabs(["🌐 Buscar en web", "📄 Subir PDF"])

    with tab1:
        col1, col2 = st.columns([3, 1])
        with col1:
            nombre_web = st.text_input(
                "Nombre del proyecto",
                placeholder="Ej: Torres del Parque, Edificio Marina, etc.",
                key="nombre_web",
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            buscar_btn = st.button("🔍 Buscar y analizar", type="primary", use_container_width=True)

        precio_uf_web = st.number_input(
            "💰 Precio del proyecto en UF",
            min_value=0.0, step=100.0, value=0.0, format="%.2f",
            help="Ingresa el precio de venta del proyecto en UF (ej: 5200.00)",
            key="precio_uf_web",
        )

        etiquetas_web = st.multiselect(
            "🏷️ Etiquetas del proyecto",
            ["Rentabilidad", "Libertad financiera", "Jubilación"],
            key="etiquetas_web",
            help="¿Para qué perfil de inversión aplica este proyecto?",
        )

        if buscar_btn and nombre_web:
            if not api_ok:
                st.error("⚠️ Configura tu API Key en el archivo .env para el proveedor seleccionado.")
            else:
                with st.status("🔍 Buscando información del proyecto...", expanded=True) as status:
                    st.write("🌐 Buscando en la web...")
                    contexto_web, resultados = analizar_proyecto_por_nombre(nombre_web)

                    if resultados and len(resultados) > 0 and "error" not in resultados[0]:
                        st.write(f"✅ Se encontraron {len(resultados)} resultados")
                        with st.expander("📄 Ver resultados de búsqueda"):
                            for r in resultados:
                                st.markdown(f"**[{r['titulo']}]({r['url']})**")
                                st.caption(r["snippet"])
                                st.markdown("---")
                    else:
                        st.write("ℹ️ No se encontró información específica en la web")

                    st.write("🤖 Generando descripción con AI...")
                    descripcion = generar_descripcion_con_ai(nombre_web, contexto_web or "")

                    if descripcion and not descripcion.startswith("Error"):
                        proyecto = add_proyecto(
                            nombre=nombre_web,
                            descripcion=descripcion,
                            fuente="web",
                            detalles_web=contexto_web or "",
                            precio_uf=precio_uf_web,
                            etiquetas=etiquetas_web,
                        )
                        status.update(label="✅ Proyecto agregado exitosamente", state="complete")
                        st.success(f"**{nombre_web}** agregado correctamente")
                        st.rerun()
                        st.stop()
                    else:
                        status.update(label="❌ Error al generar descripción", state="error")
                        st.error(descripcion or "Error desconocido")

    with tab2:
        col1, col2 = st.columns([3, 1])
        with col1:
            nombre_pdf = st.text_input(
                "Nombre del proyecto",
                placeholder="Ej: Torres del Parque, Edificio Marina, etc.",
                key="nombre_pdf",
            )
        with col2:
            st.markdown(" ")

        precio_uf_pdf = st.number_input(
            "💰 Precio del proyecto en UF",
            min_value=0.0, step=100.0, value=0.0, format="%.2f",
            help="Ingresa el precio de venta del proyecto en UF (ej: 5200.00)",
            key="precio_uf_pdf",
        )

        etiquetas_pdf = st.multiselect(
            "🏷️ Etiquetas del proyecto",
            ["Rentabilidad", "Libertad financiera", "Jubilación"],
            key="etiquetas_pdf",
            help="¿Para qué perfil de inversión aplica este proyecto?",
        )

        pdf_file = st.file_uploader(
            "Sube la presentación del proyecto (PDF)",
            type=["pdf"],
            help="Selecciona el archivo PDF con la presentación del proyecto",
        )

        if pdf_file and nombre_pdf and st.button("📄 Analizar PDF", type="primary", key="btn_pdf"):
            if not api_ok:
                st.error("⚠️ Configura tu API Key en el archivo .env para el proveedor seleccionado.")
            else:
                with st.status("📄 Analizando PDF...", expanded=True) as status:
                    st.write("📄 Extrayendo texto del PDF...")
                    texto = extraer_texto_pdf(pdf_file.read())

                    if texto.startswith("Error"):
                        status.update(label="❌ Error al leer PDF", state="error")
                        st.error(texto)
                    else:
                        st.write(f"✅ Texto extraído ({len(texto)} caracteres)")
                        st.write("🤖 Analizando con AI...")
                        descripcion = analizar_pdf_con_ai(nombre_pdf, texto)

                        if descripcion and not descripcion.startswith("Error"):
                            proyecto = add_proyecto(
                                nombre=nombre_pdf,
                                descripcion=descripcion,
                                fuente="pdf",
                                pdf_content=texto,
                                precio_uf=precio_uf_pdf,
                                etiquetas=etiquetas_pdf,
                            )
                            status.update(label="✅ Proyecto agregado exitosamente", state="complete")
                            st.success(f"**{nombre_pdf}** agregado correctamente")
                            st.rerun()
                            st.stop()
                        else:
                            status.update(label="❌ Error al analizar con AI", state="error")
                            st.error(descripcion or "Error desconocido")

# ===== LISTA DE PROYECTOS =====
st.markdown("---")
st.markdown("## Proyectos registrados")

proyectos = get_proyectos()

if not proyectos:
    st.info("📭 No hay proyectos registrados. Agrega tu primer proyecto usando el formulario de arriba.")
else:
    for p in proyectos:
        precio = p.get("precio_uf", 0)
        with st.container():
            cols = st.columns([1, 4, 1, 1])
            with cols[0]:
                icono = "🌐" if p["fuente"] == "web" else "📄"
                st.markdown(f"<h2 style='text-align:center'>{icono}</h2>", unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"### {p['nombre']}")
                st.caption(f"Fuente: {'Búsqueda web' if p['fuente'] == 'web' else 'PDF subido'} • {p['created_at'][:10]}")
                etiquetas = p.get("etiquetas", [])
                if etiquetas:
                    chips = " ".join(f":blue-background[**{e}**]" for e in etiquetas)
                    st.markdown(f"🏷️ {chips}", unsafe_allow_html=True)
                with st.expander("📖 Ver descripción"):
                    st.markdown(p["descripcion"])

                if st.session_state.get(f"editando_tags_{p['id']}", False):
                    opciones = ["Rentabilidad", "Libertad financiera", "Jubilación"]
                    nuevas_tags = st.multiselect(
                        "🏷️ Editar etiquetas",
                        opciones,
                        default=etiquetas,
                        key=f"multisel_{p['id']}",
                    )
                    if st.button("💾 Guardar etiquetas", key=f"save_tags_{p['id']}"):
                        update_proyecto(p["id"], etiquetas=nuevas_tags)
                        st.session_state[f"editando_tags_{p['id']}"] = False
                        st.rerun()
            with cols[2]:
                if precio > 0:
                    st.markdown(f"### 💰<br>{precio:,.2f} UF", unsafe_allow_html=True)
                else:
                    st.markdown("### 💰\n—", unsafe_allow_html=True)
            with cols[3]:
                col_b1, col_b2, col_b3 = st.columns(3)
                with col_b1:
                    if st.button("✏️", key=f"edit_{p['id']}", help="Editar proyecto"):
                        st.session_state[f"editando_proyecto_{p['id']}"] = True
                        st.rerun()
                with col_b2:
                    if st.button("🏷️", key=f"tag_{p['id']}", help="Editar etiquetas"):
                        st.session_state[f"editando_tags_{p['id']}"] = True
                        st.rerun()
                with col_b3:
                    if st.button("🗑️", key=f"del_{p['id']}", help="Eliminar proyecto"):
                        delete_proyecto(p["id"])
                        st.rerun()
                        st.stop()

            # ===== FORMULARIO DE EDICIÓN =====
            if st.session_state.get(f"editando_proyecto_{p['id']}", False):
                with st.container(border=True):
                    st.markdown(f"#### ✏️ Editando: {p['nombre']}")
                    edit_nombre = st.text_input("Nombre", value=p.get("nombre", ""), key=f"e_nombre_{p['id']}")
                    edit_descripcion = st.text_area("Descripción", value=p.get("descripcion", ""), key=f"e_desc_{p['id']}", height=200)
                    edit_precio = st.number_input("Precio (UF)", min_value=0.0, value=float(p.get("precio_uf", 0)), format="%.2f", key=f"e_precio_{p['id']}")
                    edit_etiquetas = st.multiselect(
                        "Etiquetas",
                        ["Rentabilidad", "Libertad financiera", "Jubilación"],
                        default=p.get("etiquetas", []),
                        key=f"e_tags_{p['id']}",
                    )
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("💾 Guardar cambios", type="primary", key=f"save_proy_{p['id']}", use_container_width=True):
                            update_proyecto(p["id"], nombre=edit_nombre, descripcion=edit_descripcion, precio_uf=edit_precio, etiquetas=edit_etiquetas)
                            st.session_state[f"editando_proyecto_{p['id']}"] = False
                            st.success("✅ Proyecto actualizado")
                            st.rerun()
                    with col_btn2:
                        if st.button("❌ Cancelar", key=f"cancel_proy_{p['id']}", use_container_width=True):
                            st.session_state[f"editando_proyecto_{p['id']}"] = False
                            st.rerun()
        
        # ===== SECCIÓN DE COTIZACIONES =====
        with st.expander(f"📝 Cotizaciones - {p['nombre']}", expanded=False):
            cotizaciones = p.get("cotizaciones", {})
            
            # Tipos de unidades requeridos
            tipos_unidades = ["Studio", "1D1B", "2D1B", "2D2B", "3D2B"]
            
            with st.form(key=f"form_cot_{p['id']}"):
                st.markdown("#### Ingresar detalles o subir PDF por tipo de unidad")
                new_cotizaciones = {}
                
                # Crear filas de 3 para que no se vea tan apretado
                rows = [tipos_unidades[i:i + 3] for i in range(0, len(tipos_unidades), 3)]
                for row in rows:
                    cols_cot = st.columns(len(row))
                    for idx, tipo in enumerate(row):
                        with cols_cot[idx]:
                            st.markdown(f"**{tipo}**")
                            prev_val = cotizaciones.get(tipo, {})
                            
                            precio_u = st.number_input("Precio UF", key=f"p_{tipo}_{p['id']}", min_value=0.0, value=float(prev_val.get("precio", 0.0)), step=100.0)
                            
                            # Opción de subir PDF por tipología
                            has_pdf = prev_val.get("has_pdf", False)
                            if has_pdf:
                                st.markdown("✅ **PDF ya cargado**")
                            
                            pdf_cot = st.file_uploader(f"Actualizar PDF {tipo}" if has_pdf else f"Subir PDF {tipo}", type=["pdf"], key=f"pdf_{tipo}_{p['id']}")
                            
                            desc_u = st.text_area("Detalles / Notas", key=f"d_{tipo}_{p['id']}", value=prev_val.get("detalles", ""), placeholder="Bono pie, bodega, etc.", height=80)
                            
                            new_cotizaciones[tipo] = {
                                "precio": precio_u, 
                                "detalles": desc_u,
                                "pdf_content": prev_val.get("pdf_content", ""),
                                "has_pdf": prev_val.get("has_pdf", False)
                            }
                            # Guardar el objeto file para procesarlo después del submit
                            if pdf_cot:
                                new_cotizaciones[tipo]["_file_obj"] = pdf_cot

                col_btn, col_info = st.columns([1, 3])
                with col_btn:
                    save_cot = st.form_submit_button("💾 Guardar y Analizar")
                
                if save_cot:
                    with st.spinner("🤖 Procesando PDFs y analizando con AI..."):
                        for tipo, datos in new_cotizaciones.items():
                            file_obj = datos.pop("_file_obj", None)
                            if file_obj:
                                texto_pdf = extraer_texto_pdf(file_obj.read())
                                if not texto_pdf.startswith("Error"):
                                    datos["pdf_content"] = texto_pdf
                                    datos["has_pdf"] = True
                                    # Intentar extraer precio del PDF si está en 0
                                    if datos["precio"] == 0:
                                        # Aquí podríamos usar un pequeño prompt para extraer el precio
                                        pass 

                        analisis_ai = analizar_cotizacion_con_ai(p['nombre'], new_cotizaciones)
                        update_proyecto(p['id'], cotizaciones=new_cotizaciones, analisis_cotizaciones=analisis_ai)
                    st.success("✅ Cotizaciones procesadas exitosamente")
                    st.rerun()

            # Mostrar análisis de la AI si existe
            if p.get("analisis_cotizaciones"):
                st.markdown("---")
                st.markdown("##### 🤖 Análisis de la AI sobre las cotizaciones")
                st.info(p["analisis_cotizaciones"])
                if any(c.get("has_pdf") for c in cotizaciones.values()):
                    st.caption("ℹ️ El análisis incluye información extraída de los PDFs subidos.")

        st.markdown("---")
