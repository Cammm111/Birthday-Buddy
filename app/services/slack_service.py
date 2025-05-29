# app/services/slack_service.py

import logging
import time
from typing import Dict
from slack_sdk.webhook import WebhookClient
logger = logging.getLogger(__name__)


_clients: Dict[str, WebhookClient] = {} # Cache WebhookClient instances by URL

# ─────────────────────────────Local cache for WebhookClient─────────────────────────────
def _get_client(webhook_url: str) -> WebhookClient: # Return a WebhookClient for each URL
    if webhook_url not in _clients:
        _clients[webhook_url] = WebhookClient(webhook_url)
    return _clients[webhook_url]

# ─────────────────────────────Post birthday message─────────────────────────────
def post_birthday_message(text: str, webhook_url: str) -> bool: # Send message to the Slack webhook at. Retries up to 3 times on rate-limit responses.
    if not webhook_url:
        logger.warning("Slack webhook URL missing — skipping message.")
        return False
    if not text:
        logger.warning("Empty Slack message — skipping post.")
        return False

    client = _get_client(webhook_url)
    max_retries = 3
    backoff = 1  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            resp = client.send(text=text)
            code = resp.status_code

            if code == 200:
                logger.info("Birthday message posted to Slack successfully.")
                return True

            if code >= 500 or code == 429: # Retry on server errors or rate limits
                logger.warning(
                    "Slack returned %d; retrying in %ds (attempt %d/%d).",
                    code, backoff, attempt, max_retries
                )
                time.sleep(backoff)
                backoff *= 2
                continue

            logger.error("Slack error %d: %s", code, resp.body) # Client error (4xx other than 429) — don’t retry
            return False

        except Exception:
            logger.exception("Exception while posting to Slack (attempt %d/%d)", attempt, max_retries)
            time.sleep(backoff)
            backoff *= 2

    logger.error("Failed to post birthday message after %d attempts.", max_retries)
    return False