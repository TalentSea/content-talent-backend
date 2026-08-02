from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from app.database import init_db
from app.middleware.cors_middleware import setup_cors_middleware
from app.middleware.db_middleware import PeeweeDBMiddleware
from app.routes.admin import (
    admin_video_router,
    admin_playlist_router,
    admin_profile_router,
    admin_comment_router
)

import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

async def scheduled_video_auto_publisher():
    """Background task running every 60s to publish due scheduled videos."""
    from app.repositories.video_repository import VideoRepository
    repo = VideoRepository()
    while True:
        try:
            count = repo.publish_due_scheduled_videos()
            if count > 0:
                logger.info(f"Auto-published {count} due scheduled videos.")
        except Exception as e:
            logger.error(f"Error in auto-publisher background loop: {str(e)}")
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    publisher_task = asyncio.create_task(scheduled_video_auto_publisher())
    yield
    publisher_task.cancel()

app = FastAPI(
    title="Creator OTT Platform API",
    description="Production-grade API for Admin Video Management, Bunny Stream Transcoding, and Playlist Curation.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None
)

setup_cors_middleware(app)
app.add_middleware(PeeweeDBMiddleware)

# Register Admin Video, Playlist, Profile & Comment routers cleanly
app.include_router(admin_video_router)
app.include_router(admin_playlist_router)
app.include_router(admin_profile_router)
app.include_router(admin_comment_router)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        swagger_js_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.9.0/swagger-ui.min.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png"
    )

@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js",
        redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png"
    )

@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint to verify backend service status.
    """
    return {"status": "healthy"}
