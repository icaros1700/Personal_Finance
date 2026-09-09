import pandas as pd
import pytest

from calculos import calc_pct, calcular_kpis, proyectar_patrimonio


def _df(rows):
    return pd.DataFrame(rows, columns=["tipo", "valor"])


class TestCalcularKpis:
    def test_ingresos_gastos_balance(self):
        df = _df([
            ("ingreso", 1000),
            ("ingreso", 500),
            ("gasto", 300),
        ])
        kpis = calcular_kpis(df)
        assert kpis["total_ingresos"] == 1500
        assert kpis["total_gastos"] == 300
        assert kpis["balance"] == 1200

    def test_tasa_ahorro(self):
        df = _df([("ingreso", 1000), ("gasto", 250)])
        kpis = calcular_kpis(df)
        assert kpis["tasa_ahorro"] == pytest.approx(75.0)

    def test_sin_ingresos_tasa_ahorro_es_cero(self):
        df = _df([("gasto", 100)])
        kpis = calcular_kpis(df)
        assert kpis["tasa_ahorro"] == 0

    def test_dataframe_vacio(self):
        df = _df([])
        kpis = calcular_kpis(df)
        assert kpis["total_ingresos"] == 0
        assert kpis["total_gastos"] == 0
        assert kpis["balance"] == 0
        assert kpis["tasa_ahorro"] == 0


class TestCalcPct:
    def test_porcentaje_normal(self):
        assert calc_pct(50, 100) == 0.5

    def test_se_limita_a_uno_cuando_supera_la_meta(self):
        assert calc_pct(150, 100) == 1.0

    def test_meta_en_cero_devuelve_cero(self):
        assert calc_pct(50, 0) == 0

    def test_real_en_cero(self):
        assert calc_pct(0, 100) == 0


class TestProyectarPatrimonio:
    def test_sin_anos_de_diferencia_devuelve_none(self):
        assert proyectar_patrimonio(1000, 30, 30, 8.0, 0) is None

    def test_edad_retiro_menor_devuelve_none(self):
        assert proyectar_patrimonio(1000, 40, 30, 8.0, 0) is None

    def test_capital_crece_con_interes_compuesto_sin_aportes(self):
        resultado = proyectar_patrimonio(1000, 30, 31, 12.0, 0)
        assert resultado["valor_futuro"] == pytest.approx(1000 * 1.01 ** 12, rel=1e-6)

    def test_ganancia_intereses_sin_aportes(self):
        resultado = proyectar_patrimonio(1000, 30, 31, 12.0, 0)
        esperado = resultado["valor_futuro"] - 1000
        assert resultado["ganancia_intereses"] == pytest.approx(esperado)

    def test_con_aportes_mensuales_incrementa_valor_futuro(self):
        sin_aportes = proyectar_patrimonio(1000, 30, 40, 8.0, 0)
        con_aportes = proyectar_patrimonio(1000, 30, 40, 8.0, 100)
        assert con_aportes["valor_futuro"] > sin_aportes["valor_futuro"]

    def test_curva_tiene_un_punto_por_cada_anio_incluyendo_el_inicial(self):
        resultado = proyectar_patrimonio(1000, 30, 35, 8.0, 0)
        assert len(resultado["curva"]) == 6  # años 30..35 inclusive
        assert resultado["curva"][0] == {"Edad": 30, "Saldo": 1000}

    def test_capital_inicial_cero_sin_aportes_no_crece(self):
        resultado = proyectar_patrimonio(0, 30, 40, 8.0, 0)
        assert resultado["valor_futuro"] == 0
