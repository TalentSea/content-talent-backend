from peewee import DatabaseProxy, SqliteDatabase

from app.config import get_settings

# Global database proxy for Peewee ORM
db_proxy = DatabaseProxy()


def init_db():
    """
    Initializes Peewee SQLite connection using DATABASE_URL.
    Enforces Write-Ahead Logging (WAL), foreign key cascading, and provisions all 23 database tables.
    """
    settings = get_settings()

    url = settings.DATABASE_URL.strip()
    db_file = url.replace("sqlite:///", "").replace("sqlite://", "").strip()
    if not db_file:
        db_file = "ott_platform.db"

    db = SqliteDatabase(
        db_file,
        pragmas={
            "journal_mode": "wal",
            "cache_size": -1 * 64000,
            "foreign_keys": 1,
            "ignore_check_constraints": 0,
            "busy_timeout": 5000,
            "synchronous": "normal",
        },
    )
    db_proxy.initialize(db)

    # Import models here to prevent circular dependency
    from app.models.ad_monetization import (
        AdImpressionEvent,
        AdMonthlySettlement,
        AdPlatformMonthlyReconciliation,
        CreatorPayoutProfile,
    )
    from app.models.admin import Admin
    from app.models.branding import Branding
    from app.models.category import Category
    from app.models.comment import Comment, CommentLike
    from app.models.featured_video import FeaturedVideo
    from app.models.payment import Payment
    from app.models.playlist import Playlist, PlaylistSave, PlaylistVideo
    from app.models.refresh_token import RefreshToken
    from app.models.subscriber import Subscriber
    from app.models.subscription_plan import SubscriptionPlan
    from app.models.user_subscription import UserSubscription
    from app.models.video import (
        Video,
        VideoLike,
        VideoSave,
        VideoViewEvent,
        WatchHistory,
    )

    if db_proxy.is_closed():
        db_proxy.connect()

    db_proxy.create_tables(
        [
            Admin,
            Branding,
            Subscriber,
            RefreshToken,
            Video,
            VideoLike,
            VideoSave,
            WatchHistory,
            VideoViewEvent,
            Playlist,
            PlaylistVideo,
            PlaylistSave,
            Comment,
            CommentLike,
            Category,
            FeaturedVideo,
            SubscriptionPlan,
            Payment,
            UserSubscription,
            AdImpressionEvent,
            AdPlatformMonthlyReconciliation,
            AdMonthlySettlement,
            CreatorPayoutProfile,
        ],
        safe=True,
    )

    if not db_proxy.is_closed():
        db_proxy.close()
