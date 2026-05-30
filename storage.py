"""
Persistencia JSON para proyectos y clientes.
Almacena los datos en data/proyectos.json y data/clientes.json
"""

import json
import os
import uuid
from datetime import datetime
import threading

_BACKUP_ENABLED = True

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PROYECTOS_FILE = os.path.join(DATA_DIR, "proyectos.json")
CLIENTES_FILE = os.path.join(DATA_DIR, "clientes.json")
PROMOCIONES_FILE = os.path.join(DATA_DIR, "promociones.json")


def _asegurar_directorio():
    """Crea el directorio data si no existe."""
    os.makedirs(DATA_DIR, exist_ok=True)


def _cargar_json(filepath):
    """Carga un archivo JSON, retorna lista vacía si no existe."""
    _asegurar_directorio()
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _guardar_json(filepath, data):
    """Guarda datos en un archivo JSON con copia de seguridad."""
    _asegurar_directorio()
    # Crear backup del archivo actual antes de sobrescribir
    if os.path.exists(filepath):
        backup_path = filepath + f".bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            import shutil
            shutil.copy2(filepath, backup_path)
        except Exception:
            pass
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    _backup_async()


def _backup_async():
    """Ejecuta backup en un hilo separado para no bloquear la UI."""
    if not _BACKUP_ENABLED:
        return
    try:
        from backup import auto_backup
        t = threading.Thread(target=auto_backup, daemon=True)
        t.start()
    except Exception:
        pass


# ========== PROYECTOS ==========

def get_proyectos():
    """Retorna la lista de proyectos."""
    return _cargar_json(PROYECTOS_FILE)


def add_proyecto(nombre, descripcion, fuente, detalles_web="", pdf_content="", precio_uf=0, etiquetas=None):
    """Agrega un nuevo proyecto."""
    proyectos = get_proyectos()
    proyecto = {
        "id": str(uuid.uuid4()),
        "nombre": nombre,
        "descripcion": descripcion,
        "fuente": fuente,  # "web" o "pdf"
        "detalles_web": detalles_web,
        "pdf_content": pdf_content,
        "precio_uf": precio_uf,
        "etiquetas": etiquetas or [],
        "created_at": datetime.now().isoformat(),
    }
    proyectos.append(proyecto)
    _guardar_json(PROYECTOS_FILE, proyectos)
    return proyecto


def update_proyecto(proyecto_id, **kwargs):
    """Actualiza un proyecto existente."""
    proyectos = get_proyectos()
    for p in proyectos:
        if p["id"] == proyecto_id:
            p.update(kwargs)
            break
    _guardar_json(PROYECTOS_FILE, proyectos)


def delete_proyecto(proyecto_id):
    """Elimina un proyecto por su ID."""
    proyectos = get_proyectos()
    proyectos = [p for p in proyectos if p["id"] != proyecto_id]
    _guardar_json(PROYECTOS_FILE, proyectos)


# ========== CLIENTES ==========

def get_clientes():
    """Retorna la lista de clientes."""
    return _cargar_json(CLIENTES_FILE)


def add_cliente(data):
    """Agrega un nuevo cliente con su ficha financiera."""
    clientes = get_clientes()
    cliente = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now().isoformat(),
    }
    cliente.update(data)
    clientes.append(cliente)
    _guardar_json(CLIENTES_FILE, clientes)
    return cliente


def update_cliente(cliente_id, **kwargs):
    """Actualiza un cliente existente."""
    clientes = get_clientes()
    for c in clientes:
        if c["id"] == cliente_id:
            c.update(kwargs)
            break
    _guardar_json(CLIENTES_FILE, clientes)


def delete_cliente(cliente_id):
    """Elimina un cliente por su ID."""
    clientes = get_clientes()
    clientes = [c for c in clientes if c["id"] != cliente_id]
    _guardar_json(CLIENTES_FILE, clientes)


def get_cliente_by_id(cliente_id):
    """Retorna un cliente por su ID."""
    clientes = get_clientes()
    for c in clientes:
        if c["id"] == cliente_id:
            return c
    return None


def get_proyecto_by_id(proyecto_id):
    """Retorna un proyecto por su ID."""
    proyectos = get_proyectos()
    for p in proyectos:
        if p["id"] == proyecto_id:
            return p
    return None


# ========== PROMOCIONES ==========

def get_promociones():
    """Retorna la lista de promociones."""
    return _cargar_json(PROMOCIONES_FILE)


def add_promocion(proyecto_id, nombre_proyecto, mes, descripcion_promocion, archivo_original=""):
    """Agrega una promoción a un proyecto."""
    promociones = get_promociones()
    promocion = {
        "id": str(uuid.uuid4()),
        "proyecto_id": proyecto_id,
        "nombre_proyecto": nombre_proyecto,
        "mes": mes,
        "descripcion_promocion": descripcion_promocion,
        "archivo_original": archivo_original,
        "created_at": datetime.now().isoformat(),
    }
    promociones.append(promocion)
    _guardar_json(PROMOCIONES_FILE, promociones)
    return promocion


def get_promociones_by_proyecto(proyecto_id):
    """Retorna las promociones de un proyecto."""
    promociones = get_promociones()
    return [p for p in promociones if p["proyecto_id"] == proyecto_id]


def get_promociones_by_mes(mes):
    """Retorna las promociones de un mes específico."""
    promociones = get_promociones()
    return [p for p in promociones if p["mes"] == mes]


def delete_promocion(promocion_id):
    """Elimina una promoción por su ID."""
    promociones = get_promociones()
    promociones = [p for p in promociones if p["id"] != promocion_id]
    _guardar_json(PROMOCIONES_FILE, promociones)


def get_meses_promociones():
    """Retorna la lista de meses que tienen promociones registradas."""
    promociones = get_promociones()
    meses = sorted(set(p["mes"] for p in promociones))
    return meses
