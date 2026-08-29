from app.routes.mobile.auth_routes import router as mobile_auth_router
from app.routes.mobile.branding_routes import router as mobile_branding_router
from app.routes.mobile.category_routes import router as mobile_category_router
from app.routes.mobile.comment_routes import router as mobile_comment_router
from app.routes.mobile.featured_video_routes import (
    router as mobile_featured_video_router,
)
from app.routes.mobile.playlist_routes import router as mobile_playlist_router
from app.routes.mobile.subscription_plan_routes import (
    router as mobile_subscription_plan_router,
)
from app.routes.mobile.video_routes import router as mobile_video_router

__all__ = [
    "mobile_auth_router",
    "mobile_branding_router",
    "mobile_category_router",
    "mobile_comment_router",
    "mobile_featured_video_router",
    "mobile_playlist_router",
    "mobile_subscription_plan_router",
    "mobile_video_router",
]
