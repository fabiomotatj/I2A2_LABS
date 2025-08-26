import os
from huggingface_hub import InferenceClient
import pandas as pd
import fitz
from tratamento import retorna_df_sem_anomalias, retorna_df_admissao, retorna_df_afastamentos, retorna_df_desligamento, retorna_df_ferias

client = InferenceClient(
    provider="nebius",
    api_key= os.environ["hf_api_key"],
)

inicio_periodo = pd.to_datetime('15/04/2025',dayfirst=True)
fim_periodo = pd.to_datetime('15/05/2025',dayfirst=True)

def identificar_intencao_usuario(pergunta):

    prompt = f"""
    O usuário está interagindo com nossa aplicação, para poder gerar uma planilha com os calculos de compra de VR para a empresa

    Ele pode, alem de gerar a planilha, fazer perguntas sobre o processo de geração do vr

    identifique a pergunta do usuário e retorne uma das seguintes opções:
    - GERAR_PLANILHA
    - EXPLICAR_PROCESSO
    - CONSULTAR_RESULTADO

    segue a pergunta do usuário:
    Pergunta:
    {pergunta}
    """

    completion = client.chat.completions.create(
        model="meta-llama/Llama-3.1-8B-Instruct",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    return completion.choices[0].message.content;

def responde_pergunta_usuario(pergunta):

    documento = extrair_texto_pdf()

    prompt = f"""
    O seguinte ducumento contém as instruçoes para a geração de vale refeição da empresa:

    {documento}

    Responda os questionamentos do usuário sobre o processo, com base nesse documento.

    Pergunta:
    {pergunta}
    """

    completion = client.chat.completions.create(
        model="meta-llama/Llama-3.1-8B-Instruct",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    return completion.choices[0].message.content;

def carreda_dados():
    ativos = pd.read_excel("dados/ativos.xlsx")
    aprendizes = pd.read_excel("dados/aprendiz.xlsx")
    estagiarios = pd.read_excel("dados/estagio.xlsx")
    ferias = pd.read_excel("dados/ferias.xlsx")
    desligados = pd.read_excel("dados/desligados.xlsx")
    admissao = pd.read_excel("dados/ADMISSAO_ABRIL.xlsx")
    sindicato_valores = pd.read_excel("dados/Base_sindicato_valor.xlsx")
    afastamentos = pd.read_excel("dados/afastamentos.xlsx")
    exterior = pd.read_excel("dados/exterior.xlsx")
    dias_uteis = pd.read_excel("dados/base_dias_uteis.xlsx")

    return {
    "ativos": ativos,
    "aprendizes": aprendizes,
    "estagiarios": estagiarios,
    "ferias": ferias,
    "desligados": desligados,
    "admissao": admissao,
    "sindicato_valores": sindicato_valores,
    "afastamentos": afastamentos,
    "exterior": exterior,
    "dias_uteis": dias_uteis,
}

def separa_consolida_dados():

    dfs = carreda_dados()

    df_sem_anomalia = retorna_df_sem_anomalias(dfs["ativos"],dfs["estagiarios"], dfs["aprendizes"], dfs["exterior"], dfs["afastamentos"], dfs["ferias"], dfs["sindicato_valores"], dfs["dias_uteis"])

    df_admissao = retorna_df_admissao(dfs["admissao"], inicio_periodo, fim_periodo, dfs["sindicato_valores"])

    df_desligamento = retorna_df_desligamento(dfs["desligados"], fim_periodo ,dfs["sindicato_valores"])

    df_ferias = retorna_df_ferias(dfs["ferias"], dfs["ativos"],dfs["sindicato_valores"])

    df_afastamentos = retorna_df_afastamentos(dfs["afastamentos"], fim_periodo, dfs["ativos"], dfs["sindicato_valores"])

    df_consolidado = pd.concat([df_sem_anomalia, df_admissao, df_desligamento, df_ferias, df_afastamentos], ignore_index=True)

    return df_consolidado

def gera_planilha():
    df_consolidado = separa_consolida_dados()

    df_consolidado.to_excel("saida/vr_mensal.xlsx", index=False)

    return "saida/vr_mensal.xlsx"

def extrair_texto_pdf() -> str:
    texto_total = ""

    # Abre o PDF
    doc = fitz.open("dados/Gerador_VR.pdf")

    for pagina in doc:
        texto = pagina.get_text()
        if texto.strip():
            texto_total += texto + "\n"

    if texto_total.strip():
        return texto_total.strip()

    doc.close()
    return texto_total.strip()