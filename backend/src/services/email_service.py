"""Email helpers for invitations."""

from __future__ import annotations

import asyncio
import os

import structlog
try:
    import resend
except Exception:  # pragma: no cover - optional dependency for local tests
    resend = None

logger = structlog.get_logger()


async def send_invite_email(*, to_email: str, invite_id: str, token: str, team_id: str, role: str) -> None:
    """Send a team invite email through Resend if API key is configured."""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key or resend is None:
        logger.info("resend_api_key_missing_skip_invite_email", email=to_email)
        return

    resend.api_key = api_key

    app_base_url = os.getenv("APP_BASE_URL", "http://localhost:4000")
    accept_link = f"{app_base_url}/invites/{invite_id}/accept?token={token}"

    payload = {
        "from": os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev"),
        "to": [to_email],
        "subject": "You have been invited to a team",
        "html": (
            f"<p>You have been invited to team <strong>{team_id}</strong> as <strong>{role}</strong>.</p>"
            f"<p>Accept invite: <a href='{accept_link}'>{accept_link}</a></p>"
        ),
    }

    try:
        await asyncio.to_thread(resend.Emails.send, payload)
    except Exception as exc:  # pragma: no cover - network/library errors
        logger.warning("resend_invite_email_failed", email=to_email, error=str(exc))


async def send_waitlist_welcome_email(*, to_email: str, full_name: str, temporary_password: str) -> None:
    """Send waitlist approval welcome email with temporary credentials."""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key or resend is None:
        logger.info("resend_api_key_missing_skip_waitlist_email", email=to_email)
        return

    resend.api_key = api_key
    app_base_url = os.getenv("APP_BASE_URL", "http://localhost:4000")

    payload = {
        "from": os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev"),
        "to": [to_email],
        "subject": "Welcome to Convergio Beta",
        "html": (
            f"<p>Hello {full_name or 'there'}, your beta access is now active.</p>"
            f"<p>Login email: <strong>{to_email}</strong></p>"
            f"<p>Temporary password: <strong>{temporary_password}</strong></p>"
            f"<p>Sign in at <a href='{app_base_url}'>{app_base_url}</a> and change your password immediately.</p>"
        ),
    }

    try:
        await asyncio.to_thread(resend.Emails.send, payload)
    except Exception as exc:  # pragma: no cover - network/library errors
        logger.warning("resend_waitlist_email_failed", email=to_email, error=str(exc))
