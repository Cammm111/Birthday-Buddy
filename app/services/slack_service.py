# app/services/slack_service.py

from slack_sdk.webhook import WebhookClient
from app.core.config import settings

WEBHOOK_URL = settings.slack_webhook_url

def post_birthday_message(text: str) -> None:
    """
    Send a plain-text (or simple Markdown) message to Slack via webhook.
    """
    if not WEBHOOK_URL:
        raise RuntimeError("Slack webhook URL is not configured in environment or .env")

    client = WebhookClient(str(WEBHOOK_URL))
    response = client.send(text=text)

    if response.status_code != 200:
        raise RuntimeError(f"Slack error {response.status_code}: {response.body}")
