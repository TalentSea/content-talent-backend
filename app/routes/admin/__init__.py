from app.routes.admin.video_routes import router as admin_video_router
from app.routes.admin.playlist_routes import router as admin_playlist_router
from app.routes.admin.subscriber_routes import router as subscriber_router
from app.routes.admin.plan_routes import router as plan_router

__all__ = ["subscriber_router", "plan_router", "admin_video_router", "admin_playlist_router"]
