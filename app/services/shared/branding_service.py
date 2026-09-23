import time

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.repositories.shared.branding_repository import BrandingRepository
from app.schemas.shared.branding_schemas import (
    BrandingBannerUploadResponse,
    BrandingLogoUploadResponse,
    BrandingResponse,
    BrandingUpdateRequest,
    ThemeColorsDTO,
    ThemeColorsUpdateRequest,
)
from app.utils.image_uploader import validate_and_upload_image


class BrandingService:
    """
    Business service layer managing tenant studio branding, identity attributes, and cloud asset uploads.
    Integrates directly with Tenant model.
    """

    def __init__(self, repo: BrandingRepository | None = None) -> None:
        self.repo = repo or BrandingRepository()

    def _to_branding_response(self, tenant) -> BrandingResponse:
        """Helper to map a Tenant ORM instance to a BrandingResponse DTO."""
        theme_dict = (
            tenant.get_theme_colors() if tenant else ThemeColorsDTO().model_dump()
        )
        return BrandingResponse(
            studio_name=tenant.name if tenant else None,
            tagline=tenant.tagline if tenant else None,
            description=tenant.description if tenant else None,
            banner_url=tenant.banner_url if tenant else None,
            logo_url=tenant.logo_url if tenant else None,
            theme=ThemeColorsDTO(**theme_dict),
            updated_at=tenant.updated_at if tenant else None,
        )

    def get_theme_colors(self, tenant_id: int) -> ThemeColorsDTO:
        """
        Retrieves the 9-token white-label studio theme palette for the active tenant.
        """
        if not tenant_id:
            return ThemeColorsDTO()
        tenant = self.repo.get_by_tenant_id(tenant_id)
        if not tenant:
            return ThemeColorsDTO()
        return ThemeColorsDTO(**tenant.get_theme_colors())

    def update_theme_colors(
        self, tenant_id: int, payload: ThemeColorsUpdateRequest
    ) -> ThemeColorsDTO:
        """
        Updates the white-label studio theme color tokens from the Admin Web Portal.
        """
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active tenant context found to update theme",
            )
        update_data = payload.model_dump(exclude_unset=True)
        updated_tenant = self.repo.update_theme_colors(tenant_id, update_data)
        return ThemeColorsDTO(**updated_tenant.get_theme_colors())


    def get_branding(self, tenant_id: int) -> BrandingResponse:
        """
        Retrieves current branding identity for the active tenant studio.
        Returns a read-only response with null fields if no record exists yet.
        """
        if not tenant_id:
            return BrandingResponse()
        tenant = self.repo.get_by_tenant_id(tenant_id)
        if not tenant:
            return BrandingResponse()
        return self._to_branding_response(tenant)

    def get_public_mobile_branding(
        self, tenant_id: int | None = None
    ) -> BrandingResponse:
        """
        Retrieves studio branding identity for mobile subscribers on app startup by tenant_id.
        """
        resolved_id = tenant_id
        if not resolved_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tenant_id authentication is required to fetch branding",
            )
        tenant = self.repo.get_by_tenant_id(resolved_id)
        if not tenant:
            return BrandingResponse()
        return self._to_branding_response(tenant)

    def update_branding(
        self, tenant_id: int, payload: BrandingUpdateRequest
    ) -> BrandingResponse:
        """
        Applies partial updates to tenant identity text attributes and returns the updated BrandingResponse.
        """
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active tenant context found to update branding",
            )
        update_data = payload.model_dump(exclude_unset=True)
        updated_tenant = self.repo.update_branding_text(tenant_id, update_data)
        return self._to_branding_response(updated_tenant)

    def upload_logo(self, tenant_id: int, file: UploadFile) -> BrandingLogoUploadResponse:
        """
        Validates and uploads a creator studio logo image to Bunny Storage.
        """
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active tenant context found to upload logo",
            )
        tenant = self.repo.get_by_tenant_id(tenant_id)
        old_logo_url = tenant.logo_url if tenant else None
        settings = get_settings()
        timestamp = int(time.time())

        cdn_url = validate_and_upload_image(
            file=file,
            storage_path_without_ext=f"assets/branding/logo_{tenant_id}_{timestamp}",
            max_size_mb=settings.MAX_LOGO_SIZE_MB,
            old_file_url=old_logo_url,
            old_file_storage_folder="assets/branding",
        )
        self.repo.update_logo_url(tenant_id, cdn_url)
        return BrandingLogoUploadResponse(logo_url=cdn_url)

    def upload_banner(
        self, tenant_id: int, file: UploadFile
    ) -> BrandingBannerUploadResponse:
        """
        Validates and uploads a creator cover banner image to Bunny Storage.
        """
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active tenant context found to upload banner",
            )
        tenant = self.repo.get_by_tenant_id(tenant_id)
        old_banner_url = tenant.banner_url if tenant else None
        settings = get_settings()
        timestamp = int(time.time())

        cdn_url = validate_and_upload_image(
            file=file,
            storage_path_without_ext=f"assets/branding/banner_{tenant_id}_{timestamp}",
            max_size_mb=settings.MAX_BANNER_SIZE_MB,
            old_file_url=old_banner_url,
            old_file_storage_folder="assets/branding",
        )
        self.repo.update_banner_url(tenant_id, cdn_url)
        return BrandingBannerUploadResponse(banner_url=cdn_url)
