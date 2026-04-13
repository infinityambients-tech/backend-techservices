import requests
import os

def send_discord_notification(message):
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("No Discord webhook URL configured")
        return
    
    data = {"content": message}
    try:
        requests.post(webhook_url, json=data)
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")
