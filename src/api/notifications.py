from __future__ import annotations

import base64
import json
import logging
import os
import smtplib
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any, Dict, List

from src.api.schemas import AlertRecord

logger = logging.getLogger("pravah.notifications")


@dataclass(frozen=True)
class NotificationSettings:
    enabled: bool
    webhook_url: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    email_from: str
    email_to: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_from: str
    twilio_to: str

    @classmethod
    def from_environment(cls) -> "NotificationSettings":
        return cls(
            enabled=os.getenv("PRAVAH_NOTIFICATIONS_ENABLED", "false").lower() == "true",
            webhook_url=os.getenv("PRAVAH_ALERT_WEBHOOK_URL", ""),
            smtp_host=os.getenv("PRAVAH_SMTP_HOST", ""),
            smtp_port=int(os.getenv("PRAVAH_SMTP_PORT", "587")),
            smtp_user=os.getenv("PRAVAH_SMTP_USER", ""),
            smtp_password=os.getenv("PRAVAH_SMTP_PASSWORD", ""),
            email_from=os.getenv("PRAVAH_ALERT_EMAIL_FROM", ""),
            email_to=os.getenv("PRAVAH_ALERT_EMAIL_TO", ""),
            twilio_account_sid=os.getenv("PRAVAH_TWILIO_ACCOUNT_SID", ""),
            twilio_auth_token=os.getenv("PRAVAH_TWILIO_AUTH_TOKEN", ""),
            twilio_from=os.getenv("PRAVAH_TWILIO_FROM", ""),
            twilio_to=os.getenv("PRAVAH_TWILIO_TO", ""),
        )

    def channel_status(self) -> Dict[str, bool]:
        return {
            "webhook": bool(self.webhook_url),
            "email": bool(self.smtp_host and self.email_from and self.email_to),
            "sms_whatsapp": bool(
                self.twilio_account_sid
                and self.twilio_auth_token
                and self.twilio_from
                and self.twilio_to
            ),
        }


def get_notification_status() -> Dict[str, Any]:
    settings = NotificationSettings.from_environment()
    channels = settings.channel_status()
    return {
        "enabled": settings.enabled,
        "channels": channels,
        "configured_channels": [name for name, configured in channels.items() if configured],
        "delivery_mode": "enabled" if settings.enabled else "disabled",
    }


def _alert_message(alert: AlertRecord) -> str:
    return (
        f"PRAVAH {alert.tier} alert\n"
        f"Station: {alert.station_name} (Gauge {alert.gauge_id})\n"
        f"Onset probability: {alert.probability:.1%}\n"
        f"Active flood probability: {alert.active_probability:.1%}\n"
        f"Recommendation: {alert.recommendation}\n"
        f"Created: {alert.created_at.isoformat()}"
    )


def _send_webhook(url: str, alert: AlertRecord, message: str) -> None:
    payload = json.dumps(
        {
            "event": "pravah.alert",
            "alert": alert.model_dump(mode="json"),
            "message": message,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status >= 300:
            raise RuntimeError(f"Webhook returned HTTP {response.status}")


def _send_email(settings: NotificationSettings, alert: AlertRecord, message: str) -> None:
    email = EmailMessage()
    email["Subject"] = f"PRAVAH {alert.tier} alert · Gauge {alert.gauge_id}"
    email["From"] = settings.email_from
    email["To"] = settings.email_to
    email.set_content(message)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(email)


def _send_twilio(settings: NotificationSettings, message: str) -> None:
    endpoint = (
        f"https://api.twilio.com/2010-04-01/Accounts/"
        f"{settings.twilio_account_sid}/Messages.json"
    )
    form = urllib.parse.urlencode(
        {
            "From": settings.twilio_from,
            "To": settings.twilio_to,
            "Body": message,
        }
    ).encode("utf-8")
    credentials = base64.b64encode(
        f"{settings.twilio_account_sid}:{settings.twilio_auth_token}".encode("utf-8")
    ).decode("ascii")
    request = urllib.request.Request(
        endpoint,
        data=form,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status >= 300:
            raise RuntimeError(f"Twilio returned HTTP {response.status}")


def dispatch_alert(alert: AlertRecord) -> Dict[str, List[str]]:
    settings = NotificationSettings.from_environment()
    result: Dict[str, List[str]] = {"sent": [], "errors": []}
    if not settings.enabled:
        return result

    message = _alert_message(alert)
    channels = settings.channel_status()
    senders = {
        "webhook": lambda: _send_webhook(settings.webhook_url, alert, message),
        "email": lambda: _send_email(settings, alert, message),
        "sms_whatsapp": lambda: _send_twilio(settings, message),
    }
    for channel, configured in channels.items():
        if not configured:
            continue
        try:
            senders[channel]()
            result["sent"].append(channel)
        except Exception as exc:
            logger.error("PRAVAH %s notification failed: %s", channel, exc)
            result["errors"].append(channel)
    return result
