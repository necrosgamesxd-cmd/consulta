"""
Módulo de backup manual vía Git/GitHub.
Solo se activa cuando el usuario hace clic en "Subir a GitHub".
Para que el push funcione, añade GITHUB_TOKEN=tu_token en .env o secrets de Streamlit.
"""

import os
import subprocess
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
GIT_LOCK = os.path.join(BASE_DIR, ".git", "index.lock")
SNAPSHOT_DIR = os.path.join(BASE_DIR, "data", "snapshots")
LOG_FILE = os.path.join(DATA_DIR, "backup_log.txt")


def _obtener_token():
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token
    try:
        import streamlit as st
        return st.secrets.get("GITHUB_TOKEN", "")
    except Exception:
        return ""


def _guardar_log(mensaje, error=""):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {mensaje}\n")
            if error:
                f.write(f"[{timestamp}] ERROR: {error}\n")
            f.write("-" * 60 + "\n")
    except Exception:
        pass


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
    token = _obtener_token()
    if not token:
        return True, ""
    ok, out, err = _git("remote", "get-url", "origin")
    if not ok:
        return False, err
    url = out.strip()
    if token in url:
        return True, ""
    if not url.startswith("https://"):
        return True, ""
    new_url = url.replace("https://", f"https://{token}@")
    _git("remote", "set-url", "origin", new_url)
    return True, ""


def _configurar_git_user():
    _git("config", "user.email", "consultor@inmobiliario.app")
    _git("config", "user.name", "RyR Consultor Inmobiliario")


def commit_y_push(mensaje=None):
    if not _esperar_lock():
        _guardar_log(f"Intento de backup: bloqueado por .git/index.lock")
        return False, "⚠️ Git ocupado. Espera unos segundos y vuelve a intentar."

    _configurar_git_user()
    ok_remote, err_remote = _configurar_remote()
    if not ok_remote:
        _guardar_log("Error configurar remote", err_remote)
        return False, f"⚠️ Error al configurar remote: {err_remote}"

    ok, out, err = _git("add", DATA_DIR)
    if not ok:
        _guardar_log("Error git add", err)
        return False, f"⚠️ Error en git add: {err}"

    ok, out, err = _git("diff", "--cached", "--quiet")
    if ok:
        _guardar_log("Sin cambios nuevos")
        return True, "✅ Datos ya están al día. Sin cambios nuevos."

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = mensaje or f"Backup manual {timestamp}"

    ok, out, err = _git("commit", "-m", msg)
    if not ok:
        _guardar_log("Error git commit", err)
        return False, f"⚠️ Error en commit: {err}"

    ok, out, err = _git("push", "origin", "main")
    if ok:
        _guardar_log(f"Backup subido a GitHub ({timestamp})")
        return True, f"✅ Backup subido a GitHub ({timestamp})"
    else:
        _guardar_log(f"Push falló", err)
        token = _obtener_token()
        if not token:
            return False, "⚠️ Push falló: no hay GITHUB_TOKEN configurado en secrets de Streamlit"
        else:
            return False, f"⚠️ Push falló: {err}"


def crear_snapshot():
    import shutil
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snap_dir = os.path.join(SNAPSHOT_DIR, f"snapshot_{timestamp}")
    try:
        shutil.copytree(DATA_DIR, snap_dir, dirs_exist_ok=True)
        for entry in os.listdir(SNAPSHOT_DIR):
            entry_path = os.path.join(SNAPSHOT_DIR, entry)
            if os.path.isdir(entry_path) and entry.startswith("snapshot_"):
                try:
                    mtime = os.path.getmtime(entry_path)
                    if (datetime.now().timestamp() - mtime) > 604800:
                        shutil.rmtree(entry_path, ignore_errors=True)
                except Exception:
                    pass
        return True, f"Snapshot guardado en data/snapshots/snapshot_{timestamp}"
    except Exception as e:
        return False, f"Error al crear snapshot: {e}"
