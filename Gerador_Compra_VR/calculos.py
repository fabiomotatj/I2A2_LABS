import pandas as pd
from datetime import datetime

def calcular_vr(row, dias_uteis_mes):
    """Calcula os dias de VR de acordo com regras"""
    dias = dias_uteis_mes

    # Ajuste para admissão
    if pd.notna(row["data_admissao"]) and row["data_admissao"].month == row["mes"]:
        dias -= row["data_admissao"].day - 1

    # Ajuste para desligamento
    if pd.notna(row["data_desligamento"]) and row["data_desligamento"].month == row["mes"]:
        if row["data_desligamento"].day <= 15 and row["ok_desligamento"] == True:
            dias = 0
        else:
            dias = min(dias, row["data_desligamento"].day)

    # Descontar férias e licenças
    dias -= row.get("faltas", 0)
    dias -= row.get("ferias", 0)
    dias -= row.get("licencas", 0)

    return max(0, dias)

def calcular_valores(df, dias_uteis_mes):
    """Aplica cálculo de VR para cada colaborador"""
    df["dias_vr"] = df.apply(lambda r: calcular_vr(r, dias_uteis_mes), axis=1)
    df["valor_total"] = df["dias_vr"] * df["valor_vr_dia"]
    df["custo_empresa"] = df["valor_total"] * 0.8   # exemplo: 80% empresa
    df["custo_funcionario"] = df["valor_total"] * 0.2
    return df

def calculo_padrao(df):
    """Aplica cálculo de VR para cada colaborador"""
    df["TOTAL"] = df["VALOR_DIARIO"] * df["DIAS_UTEIS"]
    df["CUSTO_EMPRESA"] = df["TOTAL"] * 0.8   # exemplo: 80% empresa
    df["DESCONTO"] = df["TOTAL"] * 0.2
    return df