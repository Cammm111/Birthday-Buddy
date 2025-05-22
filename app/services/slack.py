# app/services/slack.py
import os
from slack_sdk.webhook import WebhookClient

WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
print("DEBUG - SLACK_WEBHOOK_URL =", WEBHOOK_URL)


def post_birthday_message(text: str):
    """
    Send plain-text (or simple Markdown) to the default Slack channel.
    """
    if not WEBHOOK_URL:
        raise RuntimeError("SLACK_WEBHOOK_URL not set in environment/.env")

    resp = WebhookClient(WEBHOOK_URL).send(text=text)

    if resp.status_code != 200:
        raise RuntimeError(f"Slack error {resp.status_code}: {resp.body}")
