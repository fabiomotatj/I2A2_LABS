import os
from langchain.agents import Tool, initialize_agent
import xml.etree.ElementTree as ET
import fitz
import easyocr
from PIL import Image
import io
import numpy as np
import uuid
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import re
import json

apiKey = os.environ["open_ai_key"]

llm = ChatOpenAI(model="gpt-4o",api_key=apiKey)

def extrair_dados(texto_da_nota: str) -> str:

    prompt = f"""
    Extraia as seguintes informações do texto abaixo e retorne um JSON com as chaves:
    'prestador', 'cnpj', 'data', 'procedimento', 'valor_total', numero_nota, conselho, tipo_conselho.

    Texto da nota:
    {texto_da_nota}
    """
    # Criar o prompt template
    prompt_template = ChatPromptTemplate.from_template(prompt)

    # Preencher o template com o texto real da nota
    messages = prompt_template.format_messages(texto=texto_da_nota)

    # Chamar o modelo
    resultado =  llm(messages)

    return resultado.content

def extrair_dados_xml(xml_path: str) -> str:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    def percorrer(elem, prefix=''):
        linhas = []
        for child in elem:
            tag = child.tag.split('}')[-1]
            valor = child.text.strip() if child.text else ''
            if list(child):
                linhas += percorrer(child, prefix + tag + ".")
            elif valor:
                linhas.append(f"{prefix}{tag}: {valor}")
        return linhas

    texto_total =  "\n".join(percorrer(root))

    resultado =  extrair_dados(texto_total)

    return resultado

def detectar_tipo(path) -> str:

    ext = os.path.splitext(path)[1].lower()
    if ext == ".xml":
        return "xml"
    elif ext == ".txt":
        return "texto"
    elif ext in [".pdf", ".png", ".jpg", ".jpeg"]:
        return "pdf"
    else:
        return "desconhecido"

def salvar_temp(file):
    ext = file.filename.split('.')[-1]
    path = f"tmp/{uuid.uuid4()}.{ext}"
    with open(path, "wb") as f:
        f.write(file.file.read())
    return path

def extrair_dados_pdf(path: str) -> str:
    texto_total = ""
    # Abre o PDF
    doc = fitz.open(path)

    for pagina in doc:
        texto = pagina.get_text()
        if texto.strip():
            texto_total += texto + "\n"

    if texto_total.strip():
        return extrair_dados(texto_total.strip())

    reader = easyocr.Reader(['pt'], gpu=True)
    
    for pagina in doc:
        # Renderiza a página em imagem (matriz de pixels)
        pix = pagina.get_pixmap(dpi=200)
        imagem_bytes = pix.tobytes("png")

        # Converte os bytes em imagem PIL
        imagem_pil = Image.open(io.BytesIO(imagem_bytes)).convert("RGB")

        # Converte PIL para array numpy (formato aceito pelo EasyOCR)
        imagem_array = np.array(imagem_pil)

        # Usa OCR na imagem
        resultado = reader.readtext(imagem_array, detail=0)
        texto_total += "\n".join(resultado) + "\n"

    doc.close()
    
    return extrair_dados(texto_total)


tools = [
    Tool(
        name="ExtrairPDF",
        func=extrair_dados_pdf,
        description="Extrai dados de nota fiscal em PDF ou imagem usando OCR e LLM."
    ),
    Tool(
        name="ExtrairXML",
        func=extrair_dados_xml,
        description="Extrai dados de nota fiscal em XML."
    )
]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)

def rodar_agente(file):
    
    path = salvar_temp(file)

    tipo = detectar_tipo(path)
    print(f"Tipo detectado: {tipo}")

    if tipo == "xml":
        resultado = agent.run(f"Use a ferramenta ExtrairXML para processar o arquivo: {path}")
    elif tipo == "texto":
        resultado = agent.run(f"Use a ferramenta ExtrairTexto para processar o arquivo: {path}")
    elif tipo == "pdf":
        resultado = agent.run(f"Use a ferramenta ExtrairPDF para processar o arquivo: {path}")
    else:
        resultado = "Formato não suportado."

    return resultado


def retornar_json(file):
    
    path = salvar_temp(file)

    tipo = detectar_tipo(path)
    print(f"Tipo detectado: {tipo}")

    if tipo == "xml":
        resultado = extrair_dados_xml(path)
    elif tipo == "pdf":
        resultado = extrair_dados_pdf(path)
    else:
        resultado = "Formato não suportado."

    return limpar_json_resposta(resultado)


def limpar_json_resposta(resposta_llm: str):
    # Remove marcações como ```json e ```
    texto_limpo = re.sub(r"```(?:json)?\n?|```", "", resposta_llm).strip()
    
    try:
        # Primeira tentativa de parsing
        dados = json.loads(texto_limpo)
    except json.JSONDecodeError:
        # Se ainda for uma string JSON escapada, faz o parsing novamente
        dados = json.loads(json.loads(texto_limpo))
    
    return dados