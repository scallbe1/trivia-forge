from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .db import Base, SessionLocal, engine
from .routes import categories, games, media, questions, stats
from .seed import seed_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    if settings.seed_on_start:
        with SessionLocal() as db:
            seed_database(db)
    yield


app = FastAPI(title="Trivia Forge", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router)
app.include_router(questions.router)
app.include_router(media.router)
app.include_router(games.router)
app.include_router(stats.router)

settings.media_root.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(settings.media_root)), name="media")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "Trivia Forge"}


frontend = Path(__file__).resolve().parent.parent / "frontend_dist"
if frontend.exists():
    app.mount("/", StaticFiles(directory=str(frontend), html=True), name="frontend")
