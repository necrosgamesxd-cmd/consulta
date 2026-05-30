"""
Módulo de backup automático vía Git/GitHub.
Se llama después de cada guardado de datos, expone un botón manual en la UI,
y ejecuta un backup periódico cada 5 minutos.
Para que el push funcione, añade GITHUB_TOKEN=tu_token en .env
"""

import os
import subprocess
import threading
import time
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
GIT_LOCK = os.path.join(BASE_DIR, ".git", "index.lock")

INTERVALO_SEGUNDOS = 300  # 5 minutos

_hilo_periodico_activo = False

SNAPSHOT_DIR = os.path.join(BASE_DIR, "data", "snapshots")


def _obtener_token():
    """Obtiene GITHUB_TOKEN desde .env, variable de entorno o secrets de Streamlit."""
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token
    try:
        import streamlit as st
        return st.secrets.get("GITHUB_TOKEN", "")
    except Exception:
        return ""


def _run(*args, **kwargs):
    try:
        return subprocess.run(*args, **kwargs)
    except Exception:
        return None


def _git(*args, timeout=30):
    try:
        result = subprocess.run(
            ["git"] + list(args),
            capture_output=True, text=True, timeout=timeout,
            cwd=BASE_DIR,
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except Exception as e:
        return False, "", str(e)


def _esperar_lock():
    import time
    for _ in range(20):
        if not os.path.exists(GIT_LOCK):
            return True
        time.sleep(0.5)
    return False


def _configurar_remote():
    """Configura el remote con token si está disponible."""
    token = _obtener_token()
    if not token:
        return True
    ok, out, err = _git("remote", "get-url", "origin")
    if not ok:
        return False
    url = out.strip()
    if token in url:
        return True
    new_url = url.replace("https://", f"https://{token}@")
    _git("remote", "set-url", "origin", new_url)
    return True


def commit_y_push(mensaje=None):
    """
    Hace git add, commit y push de los archivos de datos.
    Retorna (ok, mensaje_para_ui).
    """
    if not _esperar_lock():
        return False, "⚠️ Git ocupado. Espera unos segundos y vuelve a intentar."

    _configurar_remote()

    ok, out, err = _git("add", DATA_DIR)
    if not ok:
        return False, f"⚠️ Error al hacer git add: {err}"

    ok, out, err = _git("diff", "--cached", "--quiet")
    if ok:
        return True, "✅ Datos ya están al día. Sin cambios nuevos."

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = mensaje or f"Auto-backup: datos actualizados {timestamp}"

    ok, out, err = _git("commit", "-m", msg)
    if not ok:
        return False, f"⚠️ Error en commit: {err[:200]}"

    ok, out, err = _git("push", "origin", "main")
    if ok:
        return True, f"✅ Backup subido a GitHub ({timestamp})"
    else:
        token = _obtener_token()
        if not token:
            return True, f"✅ Commit local OK (push pendiente: agrega GITHUB_TOKEN en .env o secrets de Streamlit)"
        else:
            return True, f"✅ Commit local OK (push falló: {err[:200]})"


def crear_snapshot():
    """
    Crea una copia local de todos los JSON de data/ con timestamp.
    No requiere git ni GitHub. Sirve como respaldo rápido antes de cambios.
    """
    import shutil
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snap_dir = os.path.join(SNAPSHOT_DIR, f"snapshot_{timestamp}")
    try:
        shutil.copytree(DATA_DIR, snap_dir, dirs_exist_ok=True)
        # Limpiar snapshots viejos (> 7 días)
        for entry in os.listdir(SNAPSHOT_DIR):
            entry_path = os.path.join(SNAPSHOT_DIR, entry)
            if os.path.isdir(entry_path) and entry.startswith("snapshot_"):
                try:
                    mtime = os.path.getmtime(entry_path)
                    if (time.time() - mtime) > 604800:  # 7 días
                        shutil.rmtree(entry_path, ignore_errors=True)
                except Exception:
                    pass
        return True, f"Snapshot guardado en data/snapshots/snapshot_{timestamp}"
    except Exception as e:
        return False, f"Error al crear snapshot: {e}"


def auto_backup(mensaje=None):
    try:
        commit_y_push(mensaje)
    except Exception:
        pass


def _backup_periodico():
    global _hilo_periodico_activo
    if _hilo_periodico_activo:
        return
    _hilo_periodico_activo = True

    def loop():
        while True:
            time.sleep(INTERVALO_SEGUNDOS)
            try:
                commit_y_push(mensaje=f"Backup periódico {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception:
                pass

    t = threading.Thread(target=loop, daemon=True)
    t.start()


def iniciar_backup_periodico():
    _backup_periodico()
