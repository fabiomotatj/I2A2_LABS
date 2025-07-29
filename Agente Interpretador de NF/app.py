from fastapi import FastAPI, UploadFile, File, HTTPException
from agent_core import rodar_agente, retornar_json
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Interpretador de Nota Fiscal",
    description="Interpretador de Nota Fiscal",
    version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou use ["http://localhost:3000"] para mais segurança
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/processar-nota")
async def processar(file: UploadFile = File(...)):
    try:
        resultado = rodar_agente(file)
        return {"status": "ok", "dados": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/retornar-dados")
async def retornar_dados(file: UploadFile = File(...)):
    try:
        resultado = retornar_json(file)

        # resultado = {
        # "prestador": "Clínica Médica Exemplo",
        # "cnpj": "12345678000100",
        # "data": "2025-07-22",
        # "procedimento": "Consulta Médica",
        # "valor_total": "300.00",
        # "numero_nota": "1234",
        # "conselho": "004533",
        # "tipo_conselho": "CRM"
        # }


        return JSONResponse(resultado)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# (Opcional) para lógica local
def main():
    print("Rodando localmente...")

if __name__ == "__main__":
    main()