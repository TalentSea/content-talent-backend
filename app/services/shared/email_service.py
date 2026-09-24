import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import HTTPException, status

from app.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Centralized transactional email service for dispatching verification codes (OTP)
    and security alerts across white-label tenants via standard SMTP (smtplib).
    """

    def _send_email(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: str,
    ) -> None:
        """
        Dispatches multipart (HTML + plain text) email via standard SMTP.
        If SMTP credentials are not configured, gracefully logs to console (Dev Mode).
        """
        settings = get_settings()

        # If SMTP is unconfigured, fall back to console logging for local dev
        if not settings.SMTP_HOST or not settings.SMTP_USERNAME:
            logger.warning(
                "[EMAIL DEV MODE] SMTP_HOST or SMTP_USERNAME not configured in .env. Falling back to console dispatch."
            )
            logger.info(
                "\n"
                + "=" * 60
                + "\n[EMAIL DISPATCH]\nTo: %s\nSubject: %s\n\n%s\n"
                + "=" * 60,
                to_email,
                subject,
                text_content,
            )
            return

        from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
        from_name = settings.SMTP_FROM_NAME or "Content Talent"
        from_header = f"{from_name} <{from_email}>"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_header
        msg["To"] = to_email

        # Attach text and html alternatives (clients prefer HTML if supported)
        part_text = MIMEText(text_content, "plain", "utf-8")
        part_html = MIMEText(html_content, "html", "utf-8")
        msg.attach(part_text)
        msg.attach(part_html)

        try:
            if settings.SMTP_USE_SSL:
                server = smtplib.SMTP_SSL(
                    settings.SMTP_HOST, settings.SMTP_PORT, timeout=15
                )
            else:
                server = smtplib.SMTP(
                    settings.SMTP_HOST, settings.SMTP_PORT, timeout=15
                )

            server.ehlo()

            if settings.SMTP_USE_TLS and not settings.SMTP_USE_SSL:
                server.starttls()
                server.ehlo()

            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

            server.send_message(msg)
            server.quit()

            logger.info(
                "[EMAIL DISPATCH] Successfully sent email '%s' to %s via %s:%s",
                subject,
                to_email,
                settings.SMTP_HOST,
                settings.SMTP_PORT,
            )
        except smtplib.SMTPAuthenticationError as e:
            logger.error("[EMAIL ERROR] SMTP authentication failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Mail server authentication failed. Please verify SMTP credentials in .env.",
            ) from e
        except Exception as e:
            logger.error("[EMAIL ERROR] Failed to send email to %s: %s", to_email, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to dispatch verification email: {e}",
            ) from e

    def send_registration_otp(
        self,
        email: str,
        code: str,
        is_linked_account: bool = False,
        studio_name: str | None = None,
    ) -> None:
        """
        Dispatches 6-digit registration verification OTP code to subscriber email.
        """
        settings = get_settings()
        brand = studio_name or settings.SMTP_FROM_NAME or "Content Talent"
        subject = f"{brand} — Verification Code: {code}"

        linked_note_html = ""
        linked_note_text = ""
        if is_linked_account:
            linked_note_html = (
                "<p style='color: #475569; font-size: 14px; margin-top: 16px;'>"
                "ℹ️ <em>This verification will link password login to your existing account while preserving all your active subscriptions and watch history.</em>"
                "</p>"
            )
            linked_note_text = "\nNote: This verification will link password login to your existing account while preserving all your active subscriptions.\n"

        text_content = (
            f"Welcome to {brand}!\n\n"
            f"Your verification code is: {code}\n\n"
            f"Please enter this 6-digit code in the app to complete your account verification.\n"
            f"This code will expire in 10 minutes.\n"
            f"{linked_note_text}\n"
            f"If you did not request this verification code, please ignore this email.\n"
        )

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 32px 16px;">
  <div style="max-width: 520px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 36px 32px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
    <h2 style="color: #0f172a; margin-top: 0; font-size: 24px; font-weight: 700; text-align: center;">Welcome to {brand}!</h2>
    <p style="color: #334155; font-size: 15px; line-height: 1.6; text-align: center; margin-top: 8px;">
      Use the verification code below to complete your account registration:
    </p>

    <div style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 18px 24px; text-align: center; margin: 28px 0;">
      <span style="font-family: 'Courier New', Courier, monospace; font-size: 34px; font-weight: 700; letter-spacing: 8px; color: #0f172a;">{code}</span>
    </div>

    <p style="color: #64748b; font-size: 13px; text-align: center; margin: 0;">
       <strong>This code expires in 10 minutes.</strong>
    </p>

    {linked_note_html}

    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 28px 0;" />
    <p style="color: #94a3b8; font-size: 12px; text-align: center; line-height: 1.5; margin: 0;">
      If you did not initiate this request, you can safely ignore this email.<br />
      © {brand}. All rights reserved.
    </p>
  </div>
</body>
</html>"""

        self._send_email(
            to_email=email,
            subject=subject,
            text_content=text_content,
            html_content=html_content,
        )

    def send_password_reset_otp(
        self,
        email: str,
        code: str,
        has_google_linked: bool = False,
        studio_name: str | None = None,
    ) -> None:
        """
        Dispatches 6-digit password reset OTP code to subscriber email.
        Includes Google Sign-In awareness note if subscriber originally signed up via Google.
        """
        settings = get_settings()
        brand = studio_name or settings.SMTP_FROM_NAME or "Content Talent"
        subject = f"{brand} — Password Reset Code: {code}"

        google_note_html = ""
        google_note_text = ""
        if has_google_linked:
            google_note_html = (
                "<p style='color: #475569; font-size: 14px; margin-top: 16px;'>"
                "ℹ️ <em>You originally signed in using Google. Setting a password will allow you to sign in using either Google or your email and password.</em>"
                "</p>"
            )
            google_note_text = "\nNote: You originally signed in using Google. Setting a password will allow you to sign in using either Google or your email and password.\n"

        text_content = (
            f"Hello from {brand},\n\n"
            f"We received a request to reset your password.\n\n"
            f"Your password reset code is: {code}\n\n"
            f"Please enter this 6-digit code in the app to reset your password.\n"
            f"This code will expire in 10 minutes.\n"
            f"{google_note_text}\n"
            f"If you did not request a password reset, please ignore this email. Your account remains completely secure.\n"
        )

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 32px 16px;">
  <div style="max-width: 520px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 36px 32px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
    <h2 style="color: #0f172a; margin-top: 0; font-size: 24px; font-weight: 700; text-align: center;">Reset Your Password</h2>
    <p style="color: #334155; font-size: 15px; line-height: 1.6; text-align: center; margin-top: 8px;">
      We received a request to reset the password for your <strong>{brand}</strong> account. Use the code below:
    </p>

    <div style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 18px 24px; text-align: center; margin: 28px 0;">
      <span style="font-family: 'Courier New', Courier, monospace; font-size: 34px; font-weight: 700; letter-spacing: 8px; color: #0f172a;">{code}</span>
    </div>

    <p style="color: #64748b; font-size: 13px; text-align: center; margin: 0;">
      ⏰ <strong>This code expires in 10 minutes.</strong>
    </p>

    {google_note_html}

    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 28px 0;" />
    <p style="color: #94a3b8; font-size: 12px; text-align: center; line-height: 1.5; margin: 0;">
      If you did not request a password reset, no further action is required. Your account is safe.<br />
      © {brand}. All rights reserved.
    </p>
  </div>
</body>
</html>"""

        self._send_email(
            to_email=email,
            subject=subject,
            text_content=text_content,
            html_content=html_content,
        )
