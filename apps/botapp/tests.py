import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from django.test import AsyncClient, SimpleTestCase
from django.urls import reverse

from apps.botapp import views


class WebhookViewTests(SimpleTestCase):
    token = "123456:TEST_TOKEN"
    secret = "testsecret"

    def setUp(self):
        self.client = AsyncClient()
        self.bot = SimpleNamespace(token=self.token)
        self.feed_update = AsyncMock()
        self.patches = [
            patch.object(views, "bot", self.bot),
            patch.object(views, "WEBHOOK_SECRET", self.secret),
            patch.object(views.dp, "feed_update", self.feed_update),
        ]
        for patcher in self.patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    async def test_webhook_rejects_missing_secret(self):
        response = await self.client.post(
            reverse("telegram_webhook", kwargs={"token": self.token}),
            data=json.dumps({"update_id": 1}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.feed_update.assert_not_awaited()

    async def test_webhook_accepts_valid_secret_and_token(self):
        payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "date": 0,
                "chat": {"id": 1, "type": "private"},
                "from": {"id": 1, "is_bot": False, "first_name": "Test"},
                "text": "/start",
                "entities": [{"type": "bot_command", "offset": 0, "length": 6}],
            },
        }
        response = await self.client.post(
            reverse("telegram_webhook", kwargs={"token": self.token}),
            data=json.dumps(payload),
            content_type="application/json",
            headers={"X-Telegram-Bot-Api-Secret-Token": self.secret},
        )

        self.assertEqual(response.status_code, 200)
        self.feed_update.assert_awaited_once()
