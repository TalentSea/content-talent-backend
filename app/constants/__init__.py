"""
Platform-wide constants and configurations for OTT subscription plan tiers.
"""

from app.constants.plans import (
    TIER_NO_ADS_FEATURES,
    TIER_WITH_ADS_FEATURES,
    get_plan_features,
)

__all__ = [
    "TIER_NO_ADS_FEATURES",
    "TIER_WITH_ADS_FEATURES",
    "get_plan_features",
]
