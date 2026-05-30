"""
Script de migración única: lee los archivos JSON existentes y los importa a SQLite.

Uso:
    python migrate_json_to_sqlite.py

Ejecutar antes del primer arranque con la nueva versión.
Si la DB ya existe, se salta la migración.
"""

import os
import sys
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "ryr.db")
JSON_FILES = {
    "proyectos.json": "proyectos",
    "clientes.json": "clientes",
    "promociones.json": "promociones",
}


def _cargar_json(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def migrate():
    if os.path.exists(DB_PATH):
        print(f"ℹ️  DB ya existe: {DB_PATH}")
        print("   Si quieres migrar de nuevo, bórrala primero.")
        return

    print("🔄 Iniciando migración JSON → SQLite...\n")

    # Importar storage para usar _get_conn
    sys.path.insert(0, os.path.dirname(__file__))
    import storage

    for filename, table in JSON_FILES.items():
        filepath = os.path.join(DATA_DIR, filename)
        registros = _cargar_json(filepath)
        if not registros:
            print(f"   ⏭️  {filename}: sin datos, saltando.")
            continue

        for item in registros:
            conn = storage._get_conn()
            if table == "proyectos":
                conn.execute(
                    """INSERT OR IGNORE INTO proyectos
                       (id, nombre, descripcion, fuente, detalles_web, pdf_content,
                        precio_uf, etiquetas, cotizaciones, analisis_cotizaciones, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item.get("id", ""),
                        item.get("nombre", ""),
                        item.get("descripcion", ""),
                        item.get("fuente", ""),
                        item.get("detalles_web", ""),
                        item.get("pdf_content", ""),
                        item.get("precio_uf", 0),
                        json.dumps(item.get("etiquetas", []), ensure_ascii=False),
                        json.dumps(item.get("cotizaciones", {}), ensure_ascii=False),
                        item.get("analisis_cotizaciones", ""),
                        item.get("created_at", datetime.now().isoformat()),
                    ),
                )
            elif table == "clientes":
                conn.execute(
                    """INSERT OR IGNORE INTO clientes
                       (id, nombre, telefono, correo, rut, estado_civil, profesion,
                        objetivo, sub_objetivo, direccion, ingresos, capacidad_inversion,
                        deudas, activos, cuentas, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item.get("id", ""),
                        item.get("nombre", ""),
                        item.get("telefono", ""),
                        item.get("correo", ""),
                        item.get("rut", ""),
                        item.get("estado_civil", ""),
                        item.get("profesion", ""),
                        item.get("objetivo", ""),
                        item.get("sub_objetivo", ""),
                        item.get("direccion", ""),
                        json.dumps(item.get("ingresos", {}), ensure_ascii=False),
                        json.dumps(item.get("capacidad_inversion", {}), ensure_ascii=False),
                        json.dumps(item.get("deudas", []), ensure_ascii=False),
                        json.dumps(item.get("activos", []), ensure_ascii=False),
                        json.dumps(item.get("cuentas", []), ensure_ascii=False),
                        item.get("created_at", datetime.now().isoformat()),
                    ),
                )
            elif table == "promociones":
                conn.execute(
                    """INSERT OR IGNORE INTO promociones
                       (id, proyecto_id, nombre_proyecto, mes, descripcion_promocion,
                        archivo_original, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item.get("id", ""),
                        item.get("proyecto_id", ""),
                        item.get("nombre_proyecto", ""),
                        item.get("mes", ""),
                        item.get("descripcion_promocion", ""),
                        item.get("archivo_original", ""),
                        item.get("created_at", datetime.now().isoformat()),
                    ),
                )
            conn.commit()
            conn.close()

        print(f"   ✅ {filename}: {len(registros)} registros migrados.")

    print(f"\n✅ Migración completada. DB: {DB_PATH}")


if __name__ == "__main__":
    migrate()
