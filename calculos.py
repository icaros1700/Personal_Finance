def calcular_kpis(df_filtered):
    total_ing = df_filtered[df_filtered["tipo"] == "ingreso"]["valor"].sum()
    total_gas = df_filtered[df_filtered["tipo"] == "gasto"]["valor"].sum()
    balance = total_ing - total_gas
    tasa_ahorro = (balance / total_ing * 100) if total_ing > 0 else 0
    return {
        "total_ingresos": total_ing,
        "total_gastos": total_gas,
        "balance": balance,
        "tasa_ahorro": tasa_ahorro,
    }


def calc_pct(real, meta):
    return min(real / meta, 1.0) if meta > 0 else 0


def proyectar_patrimonio(capital_actual, edad_actual, edad_retiro, tasa_interes_anual, aporte_mensual):
    anos = edad_retiro - edad_actual
    if anos <= 0:
        return None

    meses = anos * 12
    tasa_mensual = (tasa_interes_anual / 100) / 12

    vf_capital = capital_actual * ((1 + tasa_mensual) ** meses)
    vf_aportes = 0
    if aporte_mensual > 0:
        vf_aportes = aporte_mensual * (((1 + tasa_mensual) ** meses - 1) / tasa_mensual)

    valor_futuro = vf_capital + vf_aportes
    ganancia_intereses = valor_futuro - (capital_actual + (aporte_mensual * meses))

    data_points = []
    saldo = capital_actual
    for i in range(anos + 1):
        data_points.append({"Edad": edad_actual + i, "Saldo": saldo})
        saldo = saldo * (1 + (tasa_interes_anual / 100)) + (aporte_mensual * 12)

    return {
        "valor_futuro": valor_futuro,
        "ganancia_intereses": ganancia_intereses,
        "curva": data_points,
    }
