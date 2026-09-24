import json
import logging
from datetime import timedelta

from peewee import PeeweeException

from app.config import get_settings
from app.models.verification_code import VerificationCode
from app.utils.auth import hash_verification_code
from app.utils.date_utils import now_utc

logger = logging.getLogger(__name__)


class VerificationRepository:
    """
    Data access repository for in-flight 6-digit verification codes (OTP).
    Enforces a self-cleaning lifecycle:
    - In-flight rows are deleted immediately upon successful verification.
    - Expired codes and prior pending requests are purged opportunistically.
    """

    def cleanup_expired_and_pending(
        self, tenant_id: int, email: str | None = None
    ) -> int:
        """
        Purges expired verification codes globally and any existing pending codes for (tenant_id, email).
        """
        now = now_utc()
        try:
            deleted = (
                VerificationCode.delete()
                .where(VerificationCode.expires_at < now)
                .execute()
            )
            if email:
                deleted_pending = (
                    VerificationCode.delete()
                    .where(
                        (VerificationCode.tenant == tenant_id)
                        & (VerificationCode.email == email.lower().strip())
                    )
                    .execute()
                )
                deleted += deleted_pending
            return deleted
        except PeeweeException as e:
            logger.error("Error purging verification codes: %s", e)
            return 0

    def get_recent_code(
        self, tenant_id: int, email: str, purpose: str, within_seconds: int = 60
    ) -> VerificationCode | None:
        """
        Checks if a verification code was already dispatched for this email within the cooldown window.
        """
        cutoff = now_utc() - timedelta(seconds=within_seconds)
        try:
            return (
                VerificationCode.select()
                .where(
                    (VerificationCode.tenant == tenant_id)
                    & (VerificationCode.email == email.lower().strip())
                    & (VerificationCode.purpose == purpose)
                    & (VerificationCode.created_at > cutoff)
                )
                .order_by(VerificationCode.created_at.desc())
                .first()
            )
        except PeeweeException as e:
            logger.error("Error checking recent verification code: %s", e)
            return None

    def get_latest_code_for_email(
        self, tenant_id: int, email: str, purpose: str
    ) -> VerificationCode | None:
        """
        Retrieves the most recent unexpired verification code record for (tenant_id, email, purpose).
        """
        try:
            return (
                VerificationCode.select()
                .where(
                    (VerificationCode.tenant == tenant_id)
                    & (VerificationCode.email == email.lower().strip())
                    & (VerificationCode.purpose == purpose)
                    & (VerificationCode.expires_at > now_utc())
                )
                .order_by(VerificationCode.created_at.desc())
                .first()
            )
        except PeeweeException as e:
            logger.error("Error retrieving active verification code: %s", e)
            return None

    def store_registration_otp(
        self,
        tenant_id: int,
        email: str,
        raw_code: str,
        name: str,
        password_hash: str,
    ) -> VerificationCode:
        """
        Stores an in-flight registration OTP record containing hashed code and serialized temporary payload.
        """
        settings = get_settings()
        expires_minutes = getattr(settings, "VERIFICATION_CODE_EXPIRE_MINUTES", 10)
        self.cleanup_expired_and_pending(tenant_id, email)

        now = now_utc()
        expires_at = now + timedelta(minutes=expires_minutes)
        code_hash = hash_verification_code(raw_code)

        payload_dict = {
            "name": name.strip(),
            "password_hash": password_hash,
        }

        return VerificationCode.create(
            tenant=tenant_id,
            email=email.lower().strip(),
            code_hash=code_hash,
            purpose="registration",
            payload_data=json.dumps(payload_dict),
            attempts=0,
            expires_at=expires_at,
            created_at=now,
        )

    def store_password_reset_otp(
        self,
        tenant_id: int,
        email: str,
        raw_code: str,
    ) -> VerificationCode:
        """
        Stores an in-flight password reset OTP record.
        """
        settings = get_settings()
        expires_minutes = getattr(settings, "VERIFICATION_CODE_EXPIRE_MINUTES", 10)
        self.cleanup_expired_and_pending(tenant_id, email)

        now = now_utc()
        expires_at = now + timedelta(minutes=expires_minutes)
        code_hash = hash_verification_code(raw_code)

        return VerificationCode.create(
            tenant=tenant_id,
            email=email.lower().strip(),
            code_hash=code_hash,
            purpose="password_reset",
            payload_data=None,
            attempts=0,
            expires_at=expires_at,
            created_at=now,
        )

    def increment_attempts(self, code_record: VerificationCode) -> int:
        """
        Increments failed attempt counter on the record to prevent brute-force attacks.
        """
        code_record.attempts += 1
        code_record.save()
        return code_record.attempts

    def delete_code(self, code_id: int) -> None:
        """
        Immediately removes a verification record from the database upon successful verification.
        """
        try:
            VerificationCode.delete().where(VerificationCode.id == code_id).execute()
        except PeeweeException as e:
            logger.error("Error deleting verification code %s: %s", code_id, e)
