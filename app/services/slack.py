# app/services/slack.py
import os
from slack_sdk.webhook import WebhookClient

DEFAULT_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")

def post_birthday_message(text: str, webhook_url: str = None):
    url = webhook_url or DEFAULT_WEBHOOK
    if not url:
        raise RuntimeError("No Slack webhook URL")
    resp = WebhookClient(url).send(text=text)
    if resp.status_code != 200:
        raise RuntimeError(f"Slack error {resp.status_code}: {resp.body}")
