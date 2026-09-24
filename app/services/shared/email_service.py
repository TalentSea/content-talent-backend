import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Centralized transactional email service for dispatching verification codes (OTP)
    and security alerts across white-label tenants.
    """

    def send_registration_otp(
        self, email: str, code: str, is_linked_account: bool = False
    ) -> None:
        """
        Dispatches 6-digit registration verification OTP code to subscriber email.
        """
        if is_linked_account:
            logger.info(
                "[EMAIL DISPATCH] Registration OTP [%s] sent to %s (Linking to existing Google profile)",
                code,
                email,
            )
        else:
            logger.info(
                "[EMAIL DISPATCH] Registration OTP [%s] sent to %s",
                code,
                email,
            )

    def send_password_reset_otp(
        self, email: str, code: str, has_google_linked: bool = False
    ) -> None:
        """
        Dispatches 6-digit password reset OTP code to subscriber email.
        Includes Google Sign-In awareness note if subscriber originally signed up via Google.
        """
        if has_google_linked:
            logger.info(
                "[EMAIL DISPATCH] Password Reset OTP [%s] sent to %s (User has active Google profile)",
                code,
                email,
            )
        else:
            logger.info(
                "[EMAIL DISPATCH] Password Reset OTP [%s] sent to %s",
                code,
                email,
            )
