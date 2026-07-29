from app.routes.admin.video_routes import router as admin_video_router
from app.routes.admin.playlist_routes import router as admin_playlist_router
from app.routes.admin.profile_routes import router as admin_profile_router
from app.routes.admin.comment_routes import router as admin_comment_router

__all__ = ["admin_video_router", "admin_playlist_router", "admin_profile_router", "admin_comment_router"]
