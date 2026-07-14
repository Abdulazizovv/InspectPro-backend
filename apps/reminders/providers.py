import logging
import uuid
from abc import ABC, abstractmethod

import httpx

logger = logging.getLogger(__name__)


class BaseSmsProvider(ABC):
    @abstractmethod
    def send(self, phone: str, message: str) -> dict:
        """Send SMS. Returns dict with 'success' bool and optional 'message_id'."""


class MockSmsProvider(BaseSmsProvider):
    """Stub provider for development/testing. Logs instead of sending."""

    def send(self, phone: str, message: str) -> dict:
        message_id = f"mock_{uuid.uuid4().hex[:8]}"
        logger.info("[MockSMS] To=%s MsgId=%s Msg=%r", phone, message_id, message[:80])
        return {"success": True, "message_id": message_id}


class InfiniReachProvider(BaseSmsProvider):
    """InfiniReach Android gateway SMS provider."""

    API_URL = "https://api.infinireach.io/api/v1/messages"

    def __init__(self, api_key: str, from_phone: str, channel: str = "sms"):
        self.api_key = api_key
        self.from_phone = from_phone
        self.channel = channel

    def send(self, phone: str, message: str) -> dict:
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "to": phone,
            "message": message,
            "from": self.from_phone,
            "channel": self.channel,
        }
        resp = httpx.post(self.API_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise ValueError(f"InfiniReach error: {data}")
        logger.info("[InfiniReach] Sent to %s messageId=%s", phone, data.get("messageId"))
        return {"success": True, "message_id": data.get("messageId")}


def get_sms_provider() -> BaseSmsProvider:
    """Factory — reads SMS_PROVIDER from Django settings."""
    from django.conf import settings as dj_settings

    provider_name = getattr(dj_settings, "SMS_PROVIDER", "mock")
    if provider_name == "infinireach":
        api_key = getattr(dj_settings, "SMS_API_KEY", "")
        from_phone = getattr(dj_settings, "SMS_FROM", "")
        channel = getattr(dj_settings, "SMS_CHANNEL", "sms")
        if not api_key or not from_phone:
            logger.warning(
                "InfiniReach selected but SMS_API_KEY or SMS_FROM not configured. Falling back to Mock."
            )
            return MockSmsProvider()
        return InfiniReachProvider(api_key=api_key, from_phone=from_phone, channel=channel)
    return MockSmsProvider()
