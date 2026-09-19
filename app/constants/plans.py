"""
Standard Platform-Governed Technical Entitlements & Features for OTT Subscription Plans.

These feature lists represent actual technical platform capabilities (ad-insertion,
streaming resolution, offline downloads, concurrent device playback limits) and are
centrally managed to ensure 100% consistency across all creator studios and mobile apps.
"""

TIER_WITH_ADS_FEATURES: list[str] = [
    "Full video catalog access",
    "Standard definition (720p) streaming",
    "Occasional short advertisements",
    "1 concurrent device stream",
]

TIER_NO_ADS_FEATURES: list[str] = [
    "100% Ad-free streaming",
    "Full HD (1080p) crystal-clear resolution",
    "Offline mobile video downloads",
    "Up to 3 concurrent device screens",
    "Early access to new releases",
]


def get_plan_features(plan_type: str | None = None, display_order: int = 1) -> list[str]:
    """
    Returns the built-in technical feature list for a plan tier ('with_ads' or 'no_ads').
    """
    if plan_type == "no_ads" or (not plan_type and display_order == 2):
        return list(TIER_NO_ADS_FEATURES)
    return list(TIER_WITH_ADS_FEATURES)


