from peewee import CharField, DateTimeField, ForeignKeyField, IntegerField, TextField

from app.models.base import BaseModel
from app.models.tenant import Tenant
from app.utils.date_utils import now_utc


class VerificationCode(BaseModel):
    """
    Temporary security store for in-flight 6-digit OTP verification codes (Registration & Password Reset).
    Self-pruning: deleted immediately upon successful verification, and expired records purged opportunistically.
    """

    tenant = ForeignKeyField(
        Tenant,
        column_name="tenant_id",
        on_delete="CASCADE",
        index=True,
        backref="verification_codes",
    )
    email = CharField(max_length=255, index=True)
    code_hash = CharField(max_length=255)
    purpose = CharField(max_length=50)  # 'registration' or 'password_reset'
    payload_data = TextField(null=True)  # JSON-encoded temporary registration payload
    attempts = IntegerField(default=0)  # Brute-force lockout counter (max 5)
    expires_at = DateTimeField(index=True)
    created_at = DateTimeField(default=now_utc)

    class Meta:
        table_name = "verification_codes"
        indexes = ((("tenant", "email", "purpose"), False),)
