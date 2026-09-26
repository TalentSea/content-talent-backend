"""
Standard Platform-Governed Technical Entitlements & Features for OTT Subscription Plans.

These feature lists represent actual technical platform capabilities for the Android application
and are centrally managed to ensure 100% consistency across all creator studios and Android app screens.
All streaming features (catalog access, HD resolution, Android device playback) are identical.
Shorts are always 100% ad-free across all users; ads only appear on videos for 'with_ads' plan users.
"""

TIER_WITH_ADS_FEATURES: list[str] = [
    "Full access to all videos & shorts",
    "High-definition (HD) streaming",
    "Watch on Android phone & tablet",
    "Includes ads on videos (Shorts are ad-free)",
]

TIER_NO_ADS_FEATURES: list[str] = [
    "Full access to all videos & shorts",
    "High-definition (HD) streaming",
    "Watch on Android phone & tablet",
    "100% Ad-free on all videos & shorts",
]


def get_plan_features(
    plan_type: str | None = None, display_order: int = 1
) -> list[str]:
    """
    Returns the built-in technical feature list for a plan tier ('with_ads' or 'no_ads').
    """
    if plan_type == "no_ads" or (not plan_type and display_order == 2):
        return list(TIER_NO_ADS_FEATURES)
    return list(TIER_WITH_ADS_FEATURES)
