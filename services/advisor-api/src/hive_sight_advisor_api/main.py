from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hive_sight_advisor_api.routers import correction, query
from hive_sight_advisor_api.settings import load_settings


def create_app() -> FastAPI:
    settings = load_settings()
    app = FastAPI(title="HiveSight Advisor API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins or [],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"service": "advisor-api", "status": "ok"}

    app.include_router(query.router)
    app.include_router(correction.router)

    return app


app = create_app()
