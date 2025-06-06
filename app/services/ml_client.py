 # Cliente responsável por se comunicar com o serviço ML
import httpx

ML_API_URL = "https://sua-url-do-modelo/predict"  # url do serviço ML

async def chamar_servico_ml(transacao: dict) -> int:
    # Prepare o payload com os campos que o modelo espera
    payload = {
        "transacao_valor": transacao["transacao_valor"],
        "mesma_titularidade": transacao["mesma_titularidade"]
        # Adicionar campos que o modelo esta esperando
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(ML_API_URL, json=payload)
        response.raise_for_status()
        return response.json()["fraude"]  # Espera 0 ou 1
