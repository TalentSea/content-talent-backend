from fastapi import FastAPI
from app.middleware.cors_middleware import setup_cors_middleware
from app.middleware.db_middleware import PeeweeDBMiddleware
from app.routes.video_routes import router as video_router
from app.routes.playlist_routes import router as playlist_router

app = FastAPI(
    title="Creator OTT Platform API",
    description="Production-grade API for Video Management, Bunny Stream Transcoding, and Playlist Curation.",
    version="1.0.0"
)

setup_cors_middleware(app)
app.add_middleware(PeeweeDBMiddleware)

app.include_router(video_router)
app.include_router(playlist_router)

@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint to verify backend service status.
    """
    return {"status": "healthy"}
