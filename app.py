"""
Consultor Inmobiliario - Aplicación Principal
"""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Consultor Inmobiliario",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp header {background-color: transparent;}
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        font-size: 1.1rem;
        color: #6B7280;
    }
    .card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #E5E7EB;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===== SIDEBAR =====
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/real-estate.png", width=60)
    st.markdown("### 🏢 Consultor Inmobiliario")
    st.markdown("---")

    # Selector de proveedor AI
    from utils import verificar_api_key, PROVIDERS, get_provider_config

    provider_keys = list(PROVIDERS.keys())
    provider_labels = [PROVIDERS[p]["name"] for p in provider_keys]
    idx = provider_keys.index(st.session_state.get("ai_provider", "openrouter"))

    selected_provider = st.selectbox(
        "🧠 Proveedor AI",
        options=provider_keys,
        format_func=lambda x: PROVIDERS[x]["name"],
        index=idx,
        key="ai_provider_select",
        help="Selecciona el proveedor de AI a usar. Debes tener la API Key configurada en .env",
    )

    if selected_provider != st.session_state.get("ai_provider"):
        st.session_state.ai_provider = selected_provider
        st.rerun()

    # Verificar API Key del proveedor activo
    api_ok = verificar_api_key()
    config = get_provider_config()
    if not api_ok:
        st.warning(f"⚠️ API Key no configurada", icon="⚠️")
        st.caption(f"Configúrala abajo o en el archivo `.env`")
    else:
        st.success(f"✅ {config['name']} conectado", icon="✅")

    st.markdown("---")
    st.caption(f"Powered by {config['name']}")

    # ===== BACKUP / GIT =====
    st.markdown("### 💾 Backup")

    ultimo = st.session_state.get("ultimo_backup")
    if ultimo:
        if ultimo["ok"]:
            st.success(f"✅ {ultimo['timestamp'][:19]}")
        else:
            st.warning(f"⚠️ {ultimo['timestamp'][:19]}")
            with st.expander("🔍 Ver error completo"):
                st.code(ultimo.get("error", ultimo["mensaje"]))

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("📸 Snapshot local", use_container_width=True, type="secondary"):
            from backup import crear_snapshot
            ok, msg = crear_snapshot()
            if ok:
                st.toast(msg, icon="✅")
            else:
                st.toast(msg, icon="❌")
    with col_b2:
        if st.button("📤 Subir a GitHub", use_container_width=True, type="secondary"):
            with st.spinner("Subiendo a GitHub..."):
                from backup import commit_y_push
                ok, msg = commit_y_push(mensaje="Backup manual desde la app")
                st.session_state["ultimo_backup"] = {
                    "ok": ok,
                    "mensaje": msg,
                    "error": msg,
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }
                if ok:
                    st.toast(msg, icon="✅")
                    st.success(msg)
                else:
                    st.toast(msg, icon="❌")
                    st.error(msg)
                    with st.expander("🔍 Ver error completo"):
                        st.code(msg)

    from backup import LOG_FILE
    if st.button("📋 Ver historial de backups", use_container_width=True, type="secondary"):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                contenido = f.read()
            if contenido:
                with st.expander("📋 Historial de backups", expanded=True):
                    st.text(contenido)
            else:
                st.info("No hay registros de backup aún.")
        except FileNotFoundError:
            st.info("No hay registros de backup aún.")

# ===== NAVEGACIÓN PROFESIONAL =====
pages = {
    "Inicio": [
        st.Page("inicio.py", title="Inicio", icon="🏠", default=True),
    ],
    "Gestión": [
        st.Page("pages/1_Proyectos.py", title="Proyectos", icon="📋"),
        st.Page("pages/2_Clientes.py", title="Clientes", icon="👥"),
    ],
    "Asesoría": [
        st.Page("pages/3_Matching.py", title="Matching", icon="💬"),
    ],
    "Promociones": [
        st.Page("pages/4_Promociones.py", title="Promociones", icon="🎯"),
    ],
}

pg = st.navigation(pages, )
pg.run()
