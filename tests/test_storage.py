"""
Tests para storage.py (SQLite).
"""

import pytest
from storage import (
    add_cliente, get_clientes, get_cliente_by_id, update_cliente, delete_cliente,
    add_proyecto, get_proyectos, get_proyecto_by_id, update_proyecto, delete_proyecto,
    add_promocion, get_promociones, get_promociones_by_proyecto, get_promociones_by_mes,
    update_promocion, delete_promocion, get_meses_promociones,
)


class TestClientes:
    def test_add_cliente(self, sample_cliente_data):
        c = add_cliente(sample_cliente_data)
        assert c["id"] is not None
        assert c["nombre"] == "Juan Pérez"
        assert "created_at" in c

    def test_get_clientes(self, sample_cliente_data):
        add_cliente(sample_cliente_data)
        clientes = get_clientes()
        assert len(clientes) == 1
        assert clientes[0]["nombre"] == "Juan Pérez"

    def test_get_cliente_by_id(self, sample_cliente_data):
        c = add_cliente(sample_cliente_data)
        found = get_cliente_by_id(c["id"])
        assert found is not None
        assert found["nombre"] == "Juan Pérez"

    def test_get_cliente_by_id_not_found(self):
        assert get_cliente_by_id("nonexistent") is None

    def test_update_cliente(self, sample_cliente_data):
        c = add_cliente(sample_cliente_data)
        update_cliente(c["id"], nombre="María García")
        updated = get_cliente_by_id(c["id"])
        assert updated["nombre"] == "María García"
        assert updated["telefono"] == "+56912345678"

    def test_delete_cliente(self, sample_cliente_data):
        c = add_cliente(sample_cliente_data)
        delete_cliente(c["id"])
        assert get_cliente_by_id(c["id"]) is None

    def test_multiple_clientes_order(self, sample_cliente_data):
        c1 = add_cliente(sample_cliente_data)
        c2_data = dict(sample_cliente_data, nombre="María García")
        c2 = add_cliente(c2_data)
        clientes = get_clientes()
        assert len(clientes) == 2
        ids = [cl["id"] for cl in clientes]
        assert ids == [c2["id"], c1["id"]]  # newest first


class TestProyectos:
    def test_add_proyecto(self, sample_proyecto_data):
        p = add_proyecto(**sample_proyecto_data)
        assert p["id"] is not None
        assert p["nombre"] == "Torres del Parque"
        assert p["etiquetas"] == ["Rentabilidad", "Libertad financiera"]

    def test_get_proyectos(self, sample_proyecto_data):
        add_proyecto(**sample_proyecto_data)
        proyectos = get_proyectos()
        assert len(proyectos) == 1

    def test_get_proyecto_by_id(self, sample_proyecto_data):
        p = add_proyecto(**sample_proyecto_data)
        found = get_proyecto_by_id(p["id"])
        assert found["nombre"] == "Torres del Parque"

    def test_update_proyecto(self, sample_proyecto_data):
        p = add_proyecto(**sample_proyecto_data)
        update_proyecto(p["id"], nombre="Nuevo Nombre", precio_uf=6000)
        updated = get_proyecto_by_id(p["id"])
        assert updated["nombre"] == "Nuevo Nombre"
        assert updated["precio_uf"] == 6000

    def test_update_proyecto_json_field(self, sample_proyecto_data):
        p = add_proyecto(**sample_proyecto_data)
        update_proyecto(p["id"], etiquetas=["Jubilación"])
        updated = get_proyecto_by_id(p["id"])
        assert updated["etiquetas"] == ["Jubilación"]

    def test_delete_proyecto(self, sample_proyecto_data):
        p = add_proyecto(**sample_proyecto_data)
        delete_proyecto(p["id"])
        assert get_proyecto_by_id(p["id"]) is None


class TestPromociones:
    def test_add_promocion(self):
        promo = add_promocion(
            proyecto_id="proy-1",
            nombre_proyecto="Test Proyecto",
            mes="Julio 2026",
            descripcion_promocion="Bono pie 10%",
            archivo_original="promos.xlsx",
        )
        assert promo["id"] is not None
        assert promo["mes"] == "Julio 2026"

    def test_get_promociones(self):
        add_promocion("proy-1", "Test", "Julio 2026", "Bono 10%")
        promos = get_promociones()
        assert len(promos) == 1

    def test_get_promociones_by_proyecto(self):
        add_promocion("proy-1", "Test 1", "Julio 2026", "Bono 10%")
        add_promocion("proy-2", "Test 2", "Julio 2026", "Bono 20%")
        proy1_promos = get_promociones_by_proyecto("proy-1")
        assert len(proy1_promos) == 1
        assert proy1_promos[0]["nombre_proyecto"] == "Test 1"

    def test_get_promociones_by_mes(self):
        add_promocion("proy-1", "Test", "Julio 2026", "Bono 10%")
        add_promocion("proy-2", "Otro", "Agosto 2026", "Bono 20%")
        julio = get_promociones_by_mes("Julio 2026")
        assert len(julio) == 1

    def test_update_promocion(self):
        p = add_promocion("proy-1", "Test", "Julio 2026", "Bono 10%")
        update_promocion(p["id"], descripcion_promocion="Bono 15%")
        promos = get_promociones()
        updated = [x for x in promos if x["id"] == p["id"]][0]
        assert updated["descripcion_promocion"] == "Bono 15%"

    def test_delete_promocion(self):
        p = add_promocion("proy-1", "Test", "Julio 2026", "Bono 10%")
        delete_promocion(p["id"])
        assert len(get_promociones()) == 0

    def test_get_meses_promociones(self):
        add_promocion("proy-1", "Test", "Julio 2026", "Bono 10%")
        add_promocion("proy-2", "Otro", "Agosto 2026", "Bono 20%")
        meses = get_meses_promociones()
        assert "Julio 2026" in meses
        assert "Agosto 2026" in meses
