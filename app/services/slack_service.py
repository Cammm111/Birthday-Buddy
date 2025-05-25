# app/services/slack_service.py
import os
from slack_sdk.webhook import WebhookClient
from app.core.config import settings

WEBHOOK_URL = settings.slack_webhook_url
print("DEBUG - SLACK_WEBHOOK_URL =", WEBHOOK_URL)

def post_birthday_message(text: str):
    if not WEBHOOK_URL:
        raise RuntimeError("SLACK_WEBHOOK_URL not set in environment/.env")

    # Ensure WEBHOOK_URL is a string for the Slack SDK
    resp = WebhookClient(str(WEBHOOK_URL)).send(text=text)
    if resp.status_code != 200:
        raise RuntimeError(f"Slack error {resp.status_code}: {resp.body}")
