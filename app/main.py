from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db
from app.middleware.cors_middleware import setup_cors_middleware
from app.middleware.db_middleware import PeeweeDBMiddleware
from app.routes.video_routes import router as video_router
from app.routes.playlist_routes import router as playlist_router
from app.routes.subscriber_routes import router as subscriber_router
from app.routes.plan_routes import router as plan_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Creator OTT Platform API",
    description="Production-grade API for Video Management, Bunny Stream Transcoding, and Playlist Curation.",
    version="1.0.0",
    lifespan=lifespan
)

setup_cors_middleware(app)
app.add_middleware(PeeweeDBMiddleware)

app.include_router(video_router)
app.include_router(playlist_router)
app.include_router(subscriber_router)
app.include_router(plan_router)


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint to verify backend service status.
    """
    return {"status": "healthy"}
