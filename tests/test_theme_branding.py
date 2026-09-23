import pytest
from fastapi.testclient import TestClient
from peewee import SqliteDatabase

from app.database import db_proxy
from app.dependencies import get_current_admin, get_current_subscriber
from app.main import app
from app.models.tenant import Tenant

# In-memory SQLite database for isolated unit tests
test_db = SqliteDatabase(":memory:")


@pytest.fixture(autouse=True)
def setup_test_db():
    """Initializes in-memory database schema for Tenant tests."""
    db_proxy.initialize(test_db)
    test_db.bind([Tenant], bind_refs=False, bind_backrefs=False)
    test_db.connect()
    test_db.create_tables([Tenant])
    yield
    test_db.drop_tables([Tenant])
    test_db.close()


@pytest.fixture
def sample_tenant():
    """Provisions a sample tenant for theme tests."""
    tenant = Tenant.create(
        name="Content Talent",
        slug="content-talent",
        tagline="Exploring all interests",
        description="Your premier white-label creator OTT platform.",
    )
    return tenant


@pytest.fixture
def second_tenant():
    """Provisions a secondary tenant for multi-tenant isolation tests."""
    tenant = Tenant.create(
        name="Second Studio",
        slug="second-studio",
        tagline="Another white-label channel",
        description="Testing tenant isolation.",
    )
    return tenant


def test_tenant_model_default_theme_colors(sample_tenant):
    """Verifies that newly created tenants receive the default theme color palette."""
    colors = sample_tenant.get_theme_colors()

    assert colors["primaryColor"] == "#E50914"
    assert colors["secondaryColor"] == "#5865F2"
    assert colors["activeStateColor"] == "#5865F2"
    assert colors["mainBackgroundColor"] == "#000000"
    assert colors["cardBackgroundColor"] == "#12121A"
    assert colors["primaryTextColor"] == "#FFFFFF"
    assert colors["secondaryTextColor"] == "#9CA3AF"
    assert colors["mutedTextColor"] == "#6B7280"
    assert colors["buttonTextColor"] == "#FFFFFF"


def test_tenant_model_set_theme_colors(sample_tenant):
    """Verifies that set_theme_colors updates specified tokens and persists valid JSON."""
    sample_tenant.set_theme_colors({"primaryColor": "#FF3366"})
    sample_tenant.save()

    updated = Tenant.get_by_id(sample_tenant.id)
    colors = updated.get_theme_colors()
    assert colors["primaryColor"] == "#FF3366"
    assert colors["secondaryColor"] == "#5865F2"  # Untouched token preserved


def test_get_admin_theme_endpoint(sample_tenant):
    """Tests GET /api/v1/admin/branding/theme returns the active 9 color tokens."""
    app.dependency_overrides[get_current_admin] = lambda: {
        "user_id": 1,
        "tenant_id": sample_tenant.id,
        "role": "admin",
    }

    client = TestClient(app)
    response = client.get("/api/v1/admin/branding/theme")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["primaryColor"] == "#E50914"
    assert data["secondaryColor"] == "#5865F2"
    assert data["activeStateColor"] == "#5865F2"
    assert data["mainBackgroundColor"] == "#000000"
    assert data["cardBackgroundColor"] == "#12121A"
    assert data["primaryTextColor"] == "#FFFFFF"
    assert data["secondaryTextColor"] == "#9CA3AF"
    assert data["mutedTextColor"] == "#6B7280"
    assert data["buttonTextColor"] == "#FFFFFF"


def test_put_admin_theme_endpoint_full_update(sample_tenant):
    """Tests PUT /api/v1/admin/branding/theme modifies all 9 theme colors."""
    app.dependency_overrides[get_current_admin] = lambda: {
        "user_id": 1,
        "tenant_id": sample_tenant.id,
        "role": "admin",
    }

    payload = {
        "primaryColor": "#00E5FF",
        "secondaryColor": "#1A1A2E",
        "activeStateColor": "#00E5FF",
        "mainBackgroundColor": "#0A0A12",
        "cardBackgroundColor": "#161626",
        "primaryTextColor": "#F0F0FF",
        "secondaryTextColor": "#8888AA",
        "mutedTextColor": "#555577",
        "buttonTextColor": "#000000",
    }

    client = TestClient(app)
    response = client.put("/api/v1/admin/branding/theme", json=payload)

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data == payload

    # Verify persisted in database
    refreshed = Tenant.get_by_id(sample_tenant.id)
    assert refreshed.get_theme_colors() == payload


def test_put_admin_theme_endpoint_partial_update(sample_tenant):
    """Tests PUT /api/v1/admin/branding/theme supports partial palette updates."""
    app.dependency_overrides[get_current_admin] = lambda: {
        "user_id": 1,
        "tenant_id": sample_tenant.id,
        "role": "admin",
    }

    client = TestClient(app)
    # Update only primaryColor and activeStateColor
    response = client.put(
        "/api/v1/admin/branding/theme",
        json={"primaryColor": "#FF5722", "activeStateColor": "#FF5722"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["primaryColor"] == "#FF5722"
    assert data["activeStateColor"] == "#FF5722"
    assert data["mainBackgroundColor"] == "#000000"  # Preserved default
    assert data["primaryTextColor"] == "#FFFFFF"  # Preserved default


def test_put_admin_theme_validation_failure(sample_tenant):
    """Tests that malformed hex color codes return HTTP 422 Unprocessable Entity."""
    app.dependency_overrides[get_current_admin] = lambda: {
        "user_id": 1,
        "tenant_id": sample_tenant.id,
        "role": "admin",
    }

    client = TestClient(app)
    # Invalid hex characters
    response = client.put(
        "/api/v1/admin/branding/theme",
        json={"primaryColor": "#ZZZZZZ"},
    )
    assert response.status_code == 422

    # Missing hash prefix
    response = client.put(
        "/api/v1/admin/branding/theme",
        json={"primaryColor": "E50914"},
    )
    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_get_mobile_branding_with_theme(sample_tenant):
    """Tests GET /api/v1/mobile/branding returns studio identity and nested theme object."""
    app.dependency_overrides[get_current_subscriber] = lambda: {
        "user_id": 10,
        "tenant_id": sample_tenant.id,
        "role": "subscriber",
    }

    client = TestClient(app)
    response = client.get("/api/v1/mobile/branding")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers.get("Cache-Control") == "public, max-age=3600"

    data = response.json()
    assert data["studio_name"] == "Content Talent"
    assert data["tagline"] == "Exploring all interests"
    assert data["description"] == "Your premier white-label creator OTT platform."
    assert data["banner_url"] is None
    assert data["logo_url"] is None

    # Nested theme verified
    theme = data["theme"]
    assert theme["primaryColor"] == "#E50914"
    assert theme["secondaryColor"] == "#5865F2"
    assert theme["activeStateColor"] == "#5865F2"
    assert theme["mainBackgroundColor"] == "#000000"
    assert theme["cardBackgroundColor"] == "#12121A"
    assert theme["primaryTextColor"] == "#FFFFFF"
    assert theme["secondaryTextColor"] == "#9CA3AF"
    assert theme["mutedTextColor"] == "#6B7280"
    assert theme["buttonTextColor"] == "#FFFFFF"


def test_multi_tenant_isolation(sample_tenant, second_tenant):
    """Verifies that updating theme on Tenant 1 does not affect Tenant 2."""
    app.dependency_overrides[get_current_admin] = lambda: {
        "user_id": 1,
        "tenant_id": sample_tenant.id,
        "role": "admin",
    }

    client = TestClient(app)
    client.put(
        "/api/v1/admin/branding/theme",
        json={"primaryColor": "#123456"},
    )

    # Check Tenant 1 has updated color
    tenant_1 = Tenant.get_by_id(sample_tenant.id)
    assert tenant_1.get_theme_colors()["primaryColor"] == "#123456"

    # Check Tenant 2 still has default color
    tenant_2 = Tenant.get_by_id(second_tenant.id)
    assert tenant_2.get_theme_colors()["primaryColor"] == "#E50914"

    app.dependency_overrides.clear()
