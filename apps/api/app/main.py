from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings


app = FastAPI(
    title="Pokomon API",
    version="0.1.0",
    description="Pokemon-themed paper companion agent backend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def on_startup() -> None:
    if not settings.use_mock_services:
        from app.db.bootstrap import create_all_tables

        create_all_tables()


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Pokomon API",
        "env": settings.api_env,
        "message": "Paper companion agent backend is running.",
    }
