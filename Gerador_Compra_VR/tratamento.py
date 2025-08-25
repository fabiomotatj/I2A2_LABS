import pandas as pd
import re
from calculos import calculo_padrao
from utils import dias_uteis_periodo
from datetime import datetime

def consolidar_bases(ativos, ferias, desligados, base_cadastral, sindicato_valores, exterior, afastamentos, estagiarios, aprendizes):
    """Une todas as bases em um único DataFrame"""
    df = pd.concat([ativos, ferias, desligados, base_cadastral, exterior, afastamentos, estagiarios, aprendizes], ignore_index=True)
    df = df.merge(sindicato_valores, on="SINDICATO", how="left")
    return df

def aplicar_exclusoes(df, excluidos):
    """Remove colaboradores que não recebem VR"""
    df = df[~df["MATRICULA"].isin(excluidos)]
    return df

def corrigir_datas(df):
    """Corrige ou sinaliza datas quebradas"""
    df.loc[df["data_desligamento"] < df["data_admissao"], "data_desligamento"] = None
    return df

def retorna_df_sem_anomalias(ativos, estagiarios, aprendizes,exterior, afastamentos, ferias, sindicato_valores, dias_uteis):
    lista_exclusao = pd.concat([estagiarios["MATRICULA"], aprendizes["MATRICULA"], exterior["MATRICULA"], afastamentos["MATRICULA"], ferias["MATRICULA"]] ).unique().tolist()

    df_sem_anomalia = ativos[~ativos["MATRICULA"].isin(lista_exclusao)]

    df_sem_anomalia = df_sem_anomalia.merge(sindicato_valores, on="SINDICATO", how="left")
    df_sem_anomalia = df_sem_anomalia.merge(dias_uteis, on="SINDICATO", how="left")

    df_sem_anomalia["ADMISSAO"] = pd.to_datetime("01/01/2025",dayfirst=True, errors="coerce")

    df_sem_anomalia = calculo_padrao(df_sem_anomalia)

    return df_sem_anomalia

def retorna_df_admissao(admissao, inicio, fim, sindicato_valores ):

    df_admissao = pd.DataFrame(admissao).copy()

    df_admissao["ADMISSAO"] = pd.to_datetime(df_admissao["ADMISSAO"],dayfirst=True, errors="coerce")

    df_admissao = df_admissao[df_admissao["ADMISSAO"].between(inicio, fim)].copy()

    df_admissao["DIAS_UTEIS"] = 0;

    df_admissao["SINDICATO"] = sindicato_valores["SINDICATO"].iloc[0]
    df_admissao["VALOR_DIARIO"] = sindicato_valores["VALOR_DIARIO"].iloc[0]

    df_admissao["DIAS_UTEIS"] = df_admissao.apply(
        lambda r: dias_uteis_periodo(r["ADMISSAO"], fim),
        axis=1
    )

    df_admissao = calculo_padrao(df_admissao)
    
    df_admissao = df_admissao.drop(columns=["CARGO"])

    return df_admissao

def retorna_df_desligamento(desligamentos, fim, sindicato_valores):

    df_desligamentos = pd.DataFrame(desligamentos).copy()
    df_desligamentos["DEMISSAO"] = pd.to_datetime(df_desligamentos["DEMISSAO"],dayfirst=True, errors="coerce")

    df_desligamentos = df_desligamentos[df_desligamentos["COMUNICADO"] == "OK"].copy()

    df_desligamentos = df_desligamentos[df_desligamentos["DEMISSAO"] > pd.to_datetime("15/05/2025",dayfirst=True, errors="coerce")].copy() 
    df_desligamentos["DIAS_UTEIS"] = 0;

    df_desligamentos["ADMISSAO"] = pd.to_datetime("01/01/2025",dayfirst=True, errors="coerce")

    df_desligamentos["SINDICATO"] = sindicato_valores["SINDICATO"].iloc[0]
    df_desligamentos["VALOR_DIARIO"] = sindicato_valores["VALOR_DIARIO"].iloc[0]

    df_desligamentos["DIAS_UTEIS"] = df_desligamentos.apply(
        lambda r: dias_uteis_periodo(fim, r["DEMISSAO"]),
        axis=1
    )

    df_desligamentos = df_desligamentos.drop(columns=["DEMISSAO"])

    df_desligamentos = calculo_padrao(df_desligamentos)

    return df_desligamentos

def retorna_df_ferias(ferias, ativos, sindicato_valores):

    df_ferias = pd.DataFrame(ferias).copy()

    df_ferias = df_ferias.merge(ativos, on="MATRICULA", how="left")

    df_ferias = df_ferias.merge(sindicato_valores, on="SINDICATO", how="left")

    df_ferias["DIAS_UTEIS"] = 0;

    df_ferias["RETORNO"] = 0;

    df_ferias["DIAS_UTEIS"] = df_ferias.apply(
        lambda r: ( 22 - r["DIAS_FERIAS"]),
        axis=1
    )

    df_ferias = calculo_padrao(df_ferias)

    return df_ferias

def retorna_df_afastamentos(afastamentos, fim, ativos, sindicato_valores):

    df_afastamentos = pd.DataFrame(afastamentos).copy()

    df_afastamentos["DIAS_UTEIS"] = 0;

    df_afastamentos = df_afastamentos[df_afastamentos["OBS"].notna()]

    df_afastamentos = df_afastamentos.merge(ativos, on="MATRICULA", how="left")

    df_afastamentos = df_afastamentos.merge(sindicato_valores, on="SINDICATO", how="left")

    df_afastamentos["DIAS_UTEIS"] = df_afastamentos.apply(
        lambda r: (fim - ajusta_data(r["OBS"],fim)).days,
        axis=1
    )
    
    df_afastamentos = df_afastamentos.drop(columns=["DESC_SITUACAO"])

    df_afastamentos = df_afastamentos[df_afastamentos["DIAS_UTEIS"]>0]
    
    df_afastamentos = calculo_padrao(df_afastamentos)

    return df_afastamentos

def ajusta_data(texto, padaro):
    padrao = r"\b(\d{2}/\d{2}(?:/\d{4})?)\b"
    match = re.search(padrao, texto)

    if match:
        data_str = match.group(1)
        # Tentar converter para objeto datetime
        try:
            if len(data_str) == 5:  # formato dd/mm sem ano
                data = datetime.strptime(data_str, "%d/%m").replace(year=datetime.now().year)
            else:  # formato dd/mm/yyyy
                data = datetime.strptime(data_str, "%d/%m/%Y")
            return pd.to_datetime(data)
        except ValueError:
            return padaro
    else:
        return padrao
