import os

class Config:
    SLACK_API_TOKEN = os.environ.get("SLACK_API_TOKEN")
    # Add other config values here

config = Config()