from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import get_usuario_service
from app.api.routes.auth import router as auth_router
from app.api.routes.confrontos import router as confrontos_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.equipes import router as equipes_router
from app.api.routes.health import router as health_router
from app.api.routes.usuarios import router as usuarios_router
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_usuario_service().ensure_bootstrap_admin(
        nome=settings.bootstrap_admin_name,
        email=settings.bootstrap_admin_email,
        senha=settings.bootstrap_admin_password,
    )
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para gerenciamento dos jogos internos da faculdade.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(dashboard_router, prefix=settings.api_prefix)
app.include_router(equipes_router, prefix=settings.api_prefix)
app.include_router(confrontos_router, prefix=settings.api_prefix)
app.include_router(usuarios_router, prefix=settings.api_prefix)
