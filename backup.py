"""
Módulo de backup automático vía Git/GitHub.
Se llama después de cada guardado de datos y expone un botón manual en la UI.
Para que el push funcione, añade GITHUB_TOKEN=tu_token en .env
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
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


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
    if not GITHUB_TOKEN:
        return True
    ok, out, err = _git("remote", "get-url", "origin")
    if not ok:
        return False
    url = out.strip()
    # Si ya tiene el token incrustado, no modificar
    if GITHUB_TOKEN in url:
        return True
    # Reemplazar https://github.com/ -> https://TOKEN@github.com/
    new_url = url.replace("https://", f"https://{GITHUB_TOKEN}@")
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
        return True, f"✅ Commit local OK (push pendiente: configura GITHUB_TOKEN en .env)"


def auto_backup(mensaje=None):
    try:
        commit_y_push(mensaje)
    except Exception:
        pass
