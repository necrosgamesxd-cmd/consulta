"""
Página de inicio de RyR Consultor Inmobiliario
"""

import streamlit as st

st.markdown(
    '<div class="main-header">'
    '<div class="subtitle">RyR Consultor Inmobiliario</div>'
    '<h1>🏢 Consultor Inmobiliario</h1>'
    "<p>Asistente inteligente para matching de clientes con proyectos inmobiliarios</p></div>",
    unsafe_allow_html=True,
)

st.markdown("## ¿Qué puedes hacer aquí?")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        '<div class="card">'
        '<div class="feature-icon">📋</div>'
        "<h3>Gestionar Proyectos</h3>"
        "<p>Agrega proyectos inmobiliarios de dos formas:</p>"
        "<ul>"
        "<li><strong>Búsqueda web:</strong> Ingresa el nombre y el AI buscará información automáticamente</li>"
        "<li><strong>Subir PDF:</strong> Carga la presentación del proyecto y el AI la analizará</li>"
        "</ul>"
        "</div>",
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        '<div class="card">'
        '<div class="feature-icon">👥</div>'
        "<h3>Registrar Clientes</h3>"
        "<p>Ingresa la ficha financiera completa de cada cliente:</p>"
        "<ul>"
        "<li>Datos personales</li>"
        "<li>Ingresos y renta</li>"
        "<li>Capacidad de inversión</li>"
        "<li>Deudas, activos y cuentas</li>"
        "</ul>"
        "</div>",
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        '<div class="card">'
        '<div class="feature-icon">💬</div>'
        "<h3>Matching Inteligente</h3>"
        "<p>Selecciona un cliente y el AI (Nemotron 3 Super) te recomendará:</p>"
        "<ul>"
        "<li>Qué proyecto se adapta mejor a su perfil</li>"
        "<li>Análisis detallado de capacidad financiera</li>"
        "<li>Chat interactivo para resolver dudas</li>"
        "</ul>"
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown("---")
st.markdown("### ¿Cómo empezar?")
st.markdown(
    "1. **Configura tu API Key** en el archivo `.env` (según el proveedor que uses)\n"
    "2. Ve a **📋 Proyectos** y agrega los proyectos inmobiliarios que quieras vender\n"
    "3. Ve a **👥 Clientes** y registra los perfiles financieros de tus clientes\n"
    "4. Ve a **💬 Matching** para obtener la recomendación del AI"
)
