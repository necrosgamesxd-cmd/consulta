"""
Persistencia SQLite para proyectos, clientes y promociones.
API 100% compatible con la versión anterior (JSON).
"""

import sqlite3
import os
import uuid
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "ryr.db")


def _get_conn():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL DEFAULT '',
            descripcion TEXT DEFAULT '',
            fuente TEXT DEFAULT '',
            detalles_web TEXT DEFAULT '',
            pdf_content TEXT DEFAULT '',
            precio_uf REAL DEFAULT 0,
            etiquetas TEXT DEFAULT '[]',
            cotizaciones TEXT DEFAULT '{}',
            analisis_cotizaciones TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS clientes (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL DEFAULT '',
            telefono TEXT DEFAULT '',
            correo TEXT DEFAULT '',
            rut TEXT DEFAULT '',
            estado_civil TEXT DEFAULT '',
            profesion TEXT DEFAULT '',
            objetivo TEXT DEFAULT '',
            sub_objetivo TEXT DEFAULT '',
            direccion TEXT DEFAULT '',
            ingresos TEXT DEFAULT '{}',
            capacidad_inversion TEXT DEFAULT '{}',
            deudas TEXT DEFAULT '[]',
            activos TEXT DEFAULT '[]',
            cuentas TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS promociones (
            id TEXT PRIMARY KEY,
            proyecto_id TEXT DEFAULT '',
            nombre_proyecto TEXT DEFAULT '',
            mes TEXT DEFAULT '',
            descripcion_promocion TEXT DEFAULT '',
            archivo_original TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def _backup_db():
    import shutil
    try:
        backup_path = DB_PATH + f".bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, backup_path)
    except Exception:
        import logging
        logging.getLogger("storage").warning("No se pudo crear backup de la DB", exc_info=True)


def _row_to_dict(row):
    d = dict(row)
    for key in ("etiquetas", "cotizaciones", "ingresos", "capacidad_inversion",
                "deudas", "activos", "cuentas", "analisis_cotizaciones"):
        if key in d and isinstance(d[key], str):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


_init_db()

# ========== PROYECTOS ==========

def get_proyectos():
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM proyectos ORDER BY created_at DESC").fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def add_proyecto(nombre, descripcion, fuente, detalles_web="", pdf_content="", precio_uf=0, etiquetas=None):
    proyecto_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    conn = _get_conn()
    conn.execute(
        """INSERT INTO proyectos (id, nombre, descripcion, fuente, detalles_web, pdf_content,
           precio_uf, etiquetas, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (proyecto_id, nombre, descripcion, fuente, detalles_web, pdf_content,
         precio_uf, json.dumps(etiquetas or [], ensure_ascii=False), created_at),
    )
    conn.commit()
    conn.close()
    return {
        "id": proyecto_id,
        "nombre": nombre,
        "descripcion": descripcion,
        "fuente": fuente,
        "detalles_web": detalles_web,
        "pdf_content": pdf_content,
        "precio_uf": precio_uf,
        "etiquetas": etiquetas or [],
        "cotizaciones": {},
        "analisis_cotizaciones": "",
        "created_at": created_at,
    }


def update_proyecto(proyecto_id, **kwargs):
    conn = _get_conn()
    updates = []
    values = []
    json_fields = {"etiquetas", "cotizaciones", "analisis_cotizaciones"}
    for k, v in kwargs.items():
        if k in json_fields and not isinstance(v, str):
            v = json.dumps(v, ensure_ascii=False)
        updates.append(f"{k} = ?")
        values.append(v)
    values.append(proyecto_id)
    conn.execute(f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_proyecto(proyecto_id):
    conn = _get_conn()
    conn.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
    conn.commit()
    conn.close()


def get_proyecto_by_id(proyecto_id):
    conn = _get_conn()
    row = conn.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


# ========== CLIENTES ==========

def get_clientes():
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM clientes ORDER BY created_at DESC").fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def add_cliente(data):
    cliente_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    conn = _get_conn()
    conn.execute(
        """INSERT INTO clientes (id, nombre, telefono, correo, rut, estado_civil, profesion,
           objetivo, sub_objetivo, direccion, ingresos, capacidad_inversion, deudas, activos, cuentas, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            cliente_id,
            data.get("nombre", ""),
            data.get("telefono", ""),
            data.get("correo", ""),
            data.get("rut", ""),
            data.get("estado_civil", ""),
            data.get("profesion", ""),
            data.get("objetivo", ""),
            data.get("sub_objetivo", ""),
            data.get("direccion", ""),
            json.dumps(data.get("ingresos", {}), ensure_ascii=False),
            json.dumps(data.get("capacidad_inversion", {}), ensure_ascii=False),
            json.dumps(data.get("deudas", []), ensure_ascii=False),
            json.dumps(data.get("activos", []), ensure_ascii=False),
            json.dumps(data.get("cuentas", []), ensure_ascii=False),
            created_at,
        ),
    )
    conn.commit()
    _backup_db()
    conn.close()
    result = dict(data)
    result.update({"id": cliente_id, "created_at": created_at})
    return result


def update_cliente(cliente_id, **kwargs):
    conn = _get_conn()
    updates = []
    values = []
    json_fields = {"ingresos", "capacidad_inversion", "deudas", "activos", "cuentas"}
    for k, v in kwargs.items():
        if k in json_fields and not isinstance(v, str):
            v = json.dumps(v, ensure_ascii=False)
        updates.append(f"{k} = ?")
        values.append(v)
    values.append(cliente_id)
    conn.execute(f"UPDATE clientes SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    _backup_db()
    conn.close()


def delete_cliente(cliente_id):
    conn = _get_conn()
    conn.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    _backup_db()
    conn.close()


def get_cliente_by_id(cliente_id):
    conn = _get_conn()
    row = conn.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


# ========== PROMOCIONES ==========

def get_promociones():
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM promociones ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_promocion(proyecto_id, nombre_proyecto, mes, descripcion_promocion, archivo_original=""):
    promo_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    conn = _get_conn()
    conn.execute(
        """INSERT INTO promociones (id, proyecto_id, nombre_proyecto, mes, descripcion_promocion, archivo_original, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (promo_id, proyecto_id, nombre_proyecto, mes, descripcion_promocion, archivo_original, created_at),
    )
    conn.commit()
    conn.close()
    return {
        "id": promo_id,
        "proyecto_id": proyecto_id,
        "nombre_proyecto": nombre_proyecto,
        "mes": mes,
        "descripcion_promocion": descripcion_promocion,
        "archivo_original": archivo_original,
        "created_at": created_at,
    }


def get_promociones_by_proyecto(proyecto_id):
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM promociones WHERE proyecto_id = ? ORDER BY created_at DESC",
        (proyecto_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_promociones_by_mes(mes):
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM promociones WHERE mes = ? ORDER BY created_at DESC",
        (mes,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_promocion(promocion_id, **kwargs):
    conn = _get_conn()
    updates = []
    values = []
    for k, v in kwargs.items():
        updates.append(f"{k} = ?")
        values.append(v)
    values.append(promocion_id)
    conn.execute(f"UPDATE promociones SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_promocion(promocion_id):
    conn = _get_conn()
    conn.execute("DELETE FROM promociones WHERE id = ?", (promocion_id,))
    conn.commit()
    conn.close()


def get_meses_promociones():
    conn = _get_conn()
    rows = conn.execute("SELECT DISTINCT mes FROM promociones ORDER BY mes DESC").fetchall()
    conn.close()
    return sorted(set(r["mes"] for r in rows if r["mes"]))
