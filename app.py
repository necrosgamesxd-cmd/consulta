"""
RyR Consultor Inmobiliario - Aplicación Principal
"""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="RyR Consultor Inmobiliario",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, .stApp {
        background-color: #121212;
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }

    .stApp header {background-color: transparent;}

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        color: #ffffff !important;
    }

    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    .main-header h1 {
        font-family: 'Playfair Display', serif !important;
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        color: #D4AF37 !important;
        margin-bottom: 0.3rem;
        letter-spacing: 0.5px;
    }
    .main-header p {
        font-size: 1.1rem;
        color: #9ca3af;
        font-weight: 300;
    }
    .main-header .subtitle {
        font-size: 0.75rem;
        color: #6b7280;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-top: 4px;
    }

    .card {
        background: rgba(255,255,255,0.03);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(212,175,55,0.15);
        transition: transform 0.2s, box-shadow 0.2s;
        color: #d1d5db;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        border-color: rgba(212,175,55,0.3);
    }
    .card h3 {
        color: #ffffff !important;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
    .card ul {
        padding-left: 1.2rem;
    }
    .card li {
        margin-bottom: 0.4rem;
        font-size: 0.9rem;
    }

    .stButton button {
        background: rgba(212,175,55,0.1) !important;
        color: #D4AF37 !important;
        border: 1px solid rgba(212,175,55,0.3) !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    .stButton button:hover {
        background: rgba(212,175,55,0.2) !important;
        border-color: #D4AF37 !important;
        box-shadow: 0 2px 12px rgba(212,175,55,0.15) !important;
    }
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #D4AF37, #b8962f) !important;
        color: #121212 !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #e0b845, #D4AF37) !important;
        box-shadow: 0 4px 16px rgba(212,175,55,0.3) !important;
    }

    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox div, .stMultiselect div {
        background: rgba(255,255,255,0.05) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
        border-color: #D4AF37 !important;
        box-shadow: 0 0 0 2px rgba(212,175,55,0.15) !important;
    }

    .stDateInput input, .stTimeInput input {
        background: rgba(255,255,255,0.05) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }

    div[data-testid="stExpander"] {
        background: rgba(255,255,255,0.02) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 12px !important;
    }
    div[data-testid="stExpander"] summary {
        color: #ffffff !important;
        font-weight: 500;
    }

    .stCaption, .stMarkdown p, .stMarkdown li, .stMarkdown span {
        color: #d1d5db;
    }

    .stDataFrame, div[data-testid="stTable"] {
        background: rgba(255,255,255,0.02) !important;
        color: #ffffff !important;
    }

    .stSidebar {
        background: #0f0f1a !important;
        border-right: 1px solid rgba(255,255,255,0.05) !important;
    }
    .stSidebar .stMarkdown h3 {
        color: #D4AF37 !important;
        font-family: 'Playfair Display', serif !important;
    }

    .stAlert {
        background: rgba(212,175,55,0.08) !important;
        border: 1px solid rgba(212,175,55,0.2) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
    }
    .stAlert.stSuccess {
        background: rgba(212,175,55,0.1) !important;
        border-color: rgba(212,175,55,0.3) !important;
    }
    .stAlert.stWarning {
        background: rgba(255,183,77,0.08) !important;
        border-color: rgba(255,183,77,0.2) !important;
    }
    .stAlert.stError {
        background: rgba(239,68,68,0.08) !important;
        border-color: rgba(239,68,68,0.2) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        border-bottom-color: rgba(255,255,255,0.1) !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #9ca3af !important;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        color: #D4AF37 !important;
        border-bottom-color: #D4AF37 !important;
    }

    hr {
        border-color: rgba(255,255,255,0.06) !important;
    }

    div[data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.02) !important;
        border: 1px dashed rgba(212,175,55,0.3) !important;
        border-radius: 12px !important;
    }

    .stCheckbox label, .stRadio label {
        color: #d1d5db !important;
    }

    section[data-testid="stSidebar"] .stButton button {
        font-size: 0.8rem !important;
    }

    div[data-testid="stDownloadButton"] button {
        background: rgba(212,175,55,0.15) !important;
    }

    .st-bb, .st-at {
        background-color: transparent !important;
    }

    .st-bw, .st-bx {
        background: rgba(255,255,255,0.05) !important;
    }

    div[role="status"] {
        background: rgba(212,175,55,0.08) !important;
        border: 1px solid rgba(212,175,55,0.2) !important;
        border-radius: 12px !important;
    }

    .st-b {
        color: #D4AF37 !important;
    }

    .st-dm, .st-dl {
        color: #D4AF37 !important;
    }

    .st-spinner {
        border-color: #D4AF37 !important;
    }

    div.st-bs {
        background-color: rgba(255,255,255,0.03) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===== SIDEBAR =====
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/real-estate.png", width=60)
    st.markdown("### RyR Consultor Inmobiliario")
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

    # ===== TOKEN COUNTER =====
    st.markdown("### 📊 Consumo del día")
    tok = st.session_state.setdefault("token_usage", {"prompt": 0, "completion": 0, "total": 0})
    total = tok.get("total", 0)
    prompt = tok.get("prompt", 0)
    completion = tok.get("completion", 0)
    st.markdown(f"**{total:,}** tokens totales")
    st.caption(f"⬆️ {prompt:,} enviados · ⬇️ {completion:,} recibidos")
    limite_estimado = 1000000
    pct = min(total / limite_estimado, 1.0)
    modelo_label = "70B" if st.session_state.get("matching_tier", "super") == "super" else "8B"
    st.progress(pct, text=f"{pct*100:.1f}% del límite diario estimado ({modelo_label})")
    st.markdown("---")

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
