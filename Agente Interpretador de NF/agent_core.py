import os
from langchain.agents import Tool, initialize_agent
from langchain.chat_models import ChatOpenAI
import xml.etree.ElementTree as ET
import fitz
import easyocr
from PIL import Image
import io
import numpy as np

llm = ChatOpenAI(model="gpt-4", temperature=0)

def ler_arquivo_texto(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def extrair_dados_pdf(path: str) -> str:
    # Aqui você pode implementar OCR real; por enquanto texto simulado
    texto = "Texto extraído do PDF (simulado para exemplo)"
    prompt = f"""
    Extraia as seguintes informações do texto abaixo e retorne um JSON com as chaves:
    'prestador', 'cnpj', 'data', 'procedimento', 'valor_total'.

    Texto da nota:
    {texto}
    """
    return llm.predict(prompt)

def extrair_dados_xml(path: str) -> str:
    tree = ET.parse(path)
    root = tree.getroot()

    prestador = root.findtext(".//prestador//nome") or "Indefinido"
    cnpj = root.findtext(".//prestador//cnpj") or "Indefinido"
    procedimento = root.findtext(".//descricao") or "Indefinido"
    data = root.findtext(".//data_emissao") or "Indefinido"
    valor = root.findtext(".//valor_total") or "0.0"

    json_str = f"""{{
        "prestador": "{prestador}",
        "cnpj": "{cnpj}",
        "procedimento": "{procedimento}",
        "data": "{data}",
        "valor_total": {valor}
    }}"""
    return json_str

def extrair_dados_texto(path: str) -> str:
    texto = ler_arquivo_texto(path)
    prompt = f"""
    Extraia as seguintes informações do texto abaixo e retorne um JSON com as chaves:
    'prestador', 'cnpj', 'data', 'procedimento', 'valor_total'.

    Texto da nota:
    {texto}
    """
    return llm.predict(prompt)

def detectar_tipo(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".xml":
        return "xml"
    elif ext == ".txt":
        return "texto"
    elif ext in [".pdf", ".png", ".jpg", ".jpeg"]:
        return "pdf"
    else:
        return "desconhecido"

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
    ),
    Tool(
        name="ExtrairTexto",
        func=extrair_dados_texto,
        description="Extrai dados de nota fiscal a partir de texto simples usando LLM."
    ),
]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)

def rodar_agente(path):
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

def retorna_dados_do_pdf(path):
    reader = easyocr.Reader(['pt'], gpu=True)
    texto_total = ""

    # Abre o PDF
    doc = fitz.open(path)

    texto_total = ""

    for pagina in doc:
        texto = pagina.get_text()
        if texto.strip():
            texto_total += texto + "\n"

    if texto_total.strip():
        return texto_total.strip()

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
    return texto_total.strip()