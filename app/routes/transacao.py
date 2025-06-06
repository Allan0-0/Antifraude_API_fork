from fastapi import APIRouter, HTTPException,Query
from app.db.database import db
from bson import ObjectId  # Para lidar com ObjectId
from app.schemas.transacao_schema import TransacaoBase
from app.services.ml_client import chamar_servico_ml 
from time import sleep
import asyncio  # para pausa entre transações
from fastapi.responses import JSONResponse


router = APIRouter()

# Função para converter ObjectId para string e corrigir valores inválidos
def serialize_document(document):
    document["_id"] = str(document["_id"])
    for key, value in document.items():
        if isinstance(value, float) and (value == float("inf") or value == float("-inf") or value != value):  # Verifica NaN, inf e -inf
            document[key] = None  # Substitui valores inválidos por None
    return document

@router.get("/transacoes")
async def listar_transacoes():
    try:
        # Consultar todas as transações na coleção "todo_collection"
        transacoes = await db["todo_collection"].find().to_list(300)  # Limite de 100 documentos

        # Serializar os documentos para corrigir valores inválidos
        transacoes_serializadas = [serialize_document(doc) for doc in transacoes]

        return transacoes_serializadas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar o banco de dados: {str(e)}")


@router.post("/avaliar")
async def avaliar_transacao(transacao: TransacaoBase):
    # Aqui, os dados JÁ estão validados
    return {"dados": transacao}


# Rota para processar transações pendentes em lotes
@router.post("/transacoes/processar_pendentes")
async def processar_em_lotes(
    lote: int = Query(1000, ge=100, le=2000),
    pausa: int = Query(2, ge=0, le=10, description="Pausa entre os lotes (segundos)"),
    entre_transacoes: float = Query(0.05, ge=0.0, le=1.0, description="Pausa entre cada requisição ao ML (segundos)")
):
    """
    Processa transações pendentes em lotes controlados.
    Envia para o modelo de ML hospedado e atualiza o banco com o resultado.
    """
    total_processadas = 0
    suspeitas = 0
    normais = 0
    lote_atual = 1

    while True:
        pendentes = await db["todo_collection"].find({"status": {"$exists": False}}).to_list(length=lote)
        if not pendentes:
            break

        print(f"🔄 Lote {lote_atual}: processando {len(pendentes)} transações...")

        for transacao in pendentes:
            try:
                resultado = await chamar_servico_ml(transacao)
                status = "suspeito" if resultado == 1 else "normal"

                await db["todo_collection"].update_one(
                    {"_id": transacao["_id"]},
                    {"$set": {
                        "status": status,
                        "fraude_binario": resultado
                    }}
                )

                total_processadas += 1
                if status == "suspeito":
                    suspeitas += 1
                else:
                    normais += 1

                if entre_transacoes > 0:
                    await asyncio.sleep(entre_transacoes)

            except Exception as e:
                print(f"⚠️ Erro ao processar transação {transacao.get('transacao_id')}: {e}")

        print(f"✅ Lote {lote_atual} finalizado. Total processadas: {total_processadas}")
        lote_atual += 1

        if pausa > 0:
            sleep(pausa)

    return JSONResponse(content={
        "msg": f"{total_processadas} transações processadas com sucesso",
        "lotes_processados": lote_atual - 1,
        "normais": normais,
        "suspeitas": suspeitas
    })