"""
Fixtures compartidos para tests.
Usa un archivo temporal para la DB SQLite en cada test.
"""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))


@pytest.fixture(autouse=True)
def clean_db():
    """
    Usa un archivo temporal como DB y recrea las tablas para cada test.
    """
    import storage as st
    original_path = st.DB_PATH
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
        st.DB_PATH = temp_path
    st._init_db()
    yield
    st.DB_PATH = original_path
    try:
        os.unlink(temp_path)
    except (OSError, FileNotFoundError):
        pass


@pytest.fixture
def sample_cliente_data():
    return {
        "nombre": "Juan Pérez",
        "telefono": "+56912345678",
        "correo": "juan@email.com",
        "rut": "12.345.678-9",
        "estado_civil": "Casado/a",
        "profesion": "Ingeniero",
        "objetivo": "Invertir",
        "sub_objetivo": "Rentabilidad",
        "direccion": "Av. Siempre Viva 123",
        "ingresos": {"renta": 2500000, "dividendos": 300000, "pensiones": 0, "arriendos": 500000},
        "capacidad_inversion": {"ahorro_pie": 50000000, "cam": 800000},
        "deudas": [
            {"tipo": "Hipotecario", "institucion": "Banco Chile", "cuota": 400000,
             "total": 40000000, "nro_cuota": 120, "descontar": True}
        ],
        "activos": [{"nombre": "Depto Viña", "valor": 80000000}],
        "cuentas": [{"tipo": "Corriente", "banco": "Santander"}],
    }


@pytest.fixture
def sample_proyecto_data():
    return {
        "nombre": "Torres del Parque",
        "descripcion": "Proyecto premium en Las Condes",
        "fuente": "web",
        "detalles_web": "Información de capitalizarme.com",
        "precio_uf": 5200,
        "etiquetas": ["Rentabilidad", "Libertad financiera"],
    }
