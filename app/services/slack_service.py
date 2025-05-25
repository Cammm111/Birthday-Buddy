# app/services/slack_service.py

import logging
from slack_sdk.webhook import WebhookClient

logger = logging.getLogger(__name__)

def post_birthday_message(text: str, webhook_url: str):
    """
    Post a Slack message to the specified webhook URL.
    """
    if not webhook_url:
        logger.warning("⚠️ Slack webhook URL missing — skipping message.")
        return

    try:
        resp = WebhookClient(webhook_url).send(text=text)

        if resp.status_code == 200:
            logger.info("✅ Birthday message posted to Slack successfully.")
        else:
            logger.error(f"❌ Slack error {resp.status_code}: {resp.body}")
    except Exception as e:
        logger.exception(f"❌ Exception while posting to Slack: {e}")
