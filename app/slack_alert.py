from slack_sdk.webhook import WebhookClient
from dotenv import load_dotenv
import os

load_dotenv()

webhook_url = os.getenv('SLACK_WEBHOOK_URL')

def send_slack_notification(message):
    webhook = WebhookClient(webhook_url)
    response = webhook.send(
        text=message
    )
    if response.status_code != 200:
        raise ValueError(f"Request to slack returned an error: {response.status_code}, {response.text}")