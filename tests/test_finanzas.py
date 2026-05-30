"""
Tests para funciones financieras (utils/finanzas.py).
"""

import pytest
from utils.finanzas import calcular_limite_uf, obtener_valor_uf, VALOR_UF_FALLBACK


class TestCalcularLimiteUF:
    def test_ingresos_cero(self):
        assert calcular_limite_uf(0) == 200

    def test_ingresos_positivos(self):
        resultado = calcular_limite_uf(1250000)
        assert resultado == pytest.approx(2200.0)

    def test_ingresos_altos(self):
        resultado = calcular_limite_uf(5000000)
        assert resultado == pytest.approx(8200.0)

    def test_formula_correcta(self):
        ingresos = 2500000
        esperado = (ingresos / 625) + 200
        assert calcular_limite_uf(ingresos) == esperado


class TestObtenerValorUF:
    def test_retorna_float(self):
        valor = obtener_valor_uf()
        assert isinstance(valor, (int, float))
        assert valor > 0

    def test_no_falla_red(self):
        valor = obtener_valor_uf()
        assert valor > 1000  # Mínimo razonable
