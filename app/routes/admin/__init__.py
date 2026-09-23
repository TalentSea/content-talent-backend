from app.routes.admin.admin_user_routes import router as admin_user_router
from app.routes.admin.auth_routes import router as admin_auth_router
from app.routes.admin.branding_routes import router as admin_branding_router
from app.routes.admin.category_routes import router as admin_category_router
from app.routes.admin.comment_routes import router as admin_comment_router
from app.routes.admin.dashboard_routes import router as admin_dashboard_router
from app.routes.admin.featured_video_routes import (
    router as admin_featured_video_router,
)
from app.routes.admin.monetization_routes import (
    router as admin_monetization_router,
)
from app.routes.admin.playlist_routes import router as admin_playlist_router
from app.routes.admin.profile_routes import router as admin_profile_router
from app.routes.admin.subscription_plan_routes import (
    router as admin_subscription_plan_router,
)
from app.routes.admin.super_admin_monetization_routes import (
    router as super_admin_monetization_router,
)
from app.routes.admin.tenant_routes import router as admin_tenant_router
from app.routes.admin.video_routes import router as admin_video_router

__all__ = [
    "admin_auth_router",
    "admin_branding_router",
    "admin_category_router",
    "admin_comment_router",
    "admin_dashboard_router",
    "admin_featured_video_router",
    "admin_monetization_router",
    "admin_playlist_router",
    "admin_profile_router",
    "admin_subscription_plan_router",
    "admin_tenant_router",
    "admin_user_router",
    "admin_video_router",
    "super_admin_monetization_router",
]
