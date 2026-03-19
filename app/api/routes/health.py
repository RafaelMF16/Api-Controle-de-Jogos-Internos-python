from fastapi import APIRouter

router = APIRouter(tags=["Health"])


# Confirma se a API esta online e pronta para receber requisicoes do front-end.
@router.get("/health", summary="Verificar saude da API")
def health_check() -> dict:
    return {"status": "ok"}
