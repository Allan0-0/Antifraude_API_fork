from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.transacao import router as transacao_router

from app.routes import (
    notificacoes,
    fraude,
    contas,
    dashboard
)
app = FastAPI()

# CORS para liberar o acesso do front
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # trocar origem quando hospedar front 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Registrar as rotas
app.include_router(transacao_router, tags=["Transações"])
app.include_router(fraude.router, tags=["Verificação de Fraude"])
app.include_router(notificacoes.router, tags=["Notificações"])


# Rota para indicar que a API iniciou
@app.get("/")
async def root():
    return {"mensagem": "API Antifraude iniciada com sucesso!"} 
