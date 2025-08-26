from fastapi import FastAPI
from agent_core import identificar_intencao_usuario, gera_planilha, responde_pergunta_usuario
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI(
    title="Pré atendimento",
    description="Pré atendimento",
    version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou use ["http://localhost:3000"] para mais segurança
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    

class Requisicao(BaseModel):
    pergunta: str

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/chat.html")
    
@app.post("/chat")
def chat(req: Requisicao):
    intent = identificar_intencao_usuario(req.pergunta) 

    if "EXPLICAR_PROCESSO" in intent:
        return JSONResponse({"resposta": responde_pergunta_usuario(req.pergunta)})
    elif "CONSULTAR_RESULTADO" in intent:
        return JSONResponse({"resposta": "Foram encontrados 50 funcionários ativos."})
    elif "GERAR_PLANILHA" in intent:
        # gera a planilha

        file_path = gera_planilha()

        # retorna o arquivo
        return FileResponse(file_path, filename="vr_mensal.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


    return JSONResponse({"answer": "Posso gerar planilhas ou responder dúvidas sobre o processo."})


# (Opcional) para lógica local
def main():
    print("Rodando localmente...")

if __name__ == "__main__":
    main()