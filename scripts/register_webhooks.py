#!/usr/bin/env python3
"""
Utility script to programmatically register and inspect Shopify Webhooks.
Using this script guarantees webhooks are registered through the Custom App,
meaning Shopify signs them with the Custom App API Secret.
"""
import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_SHOP_DOMAIN = os.getenv("SHOPIFY_SHOP_DOMAIN", "0efjx4-fp.myshopify.com").strip()
SHOPIFY_ADMIN_API_ACCESS_TOKEN = os.getenv("SHOPIFY_ADMIN_API_ACCESS_TOKEN", "").strip()

API_VERSION = "2024-01"
BASE_URL = f"https://{SHOPIFY_SHOP_DOMAIN}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def list_webhooks():
    url = f"{BASE_URL}/webhooks.json"
    response = httpx.get(url, headers=HEADERS)
    if response.status_code == 200:
        webhooks = response.json().get("webhooks", [])
        print(f"Active Webhooks ({len(webhooks)}):")
        for wh in webhooks:
            print(f"  - ID: {wh['id']} | Topic: {wh['topic']} | Address: {wh['address']}")
        return webhooks
    else:
        print(f"Failed to list webhooks: {response.status_code} - {response.text}")
        return []

def register_webhook(topic: str, address: str):
    url = f"{BASE_URL}/webhooks.json"
    payload = {
        "webhook": {
            "topic": topic,
            "address": address,
            "format": "json"
        }
    }
    response = httpx.post(url, headers=HEADERS, json=payload)
    if response.status_code in (200, 201):
        wh = response.json().get("webhook", {})
        print(f"[✓] Registered webhook {topic} -> {address} (ID: {wh.get('id')})")
    else:
        print(f"[✗] Failed to register {topic}: {response.status_code} - {response.text}")

def delete_webhook(webhook_id: int):
    url = f"{BASE_URL}/webhooks/{webhook_id}.json"
    response = httpx.delete(url, headers=HEADERS)
    if response.status_code == 200:
        print(f"[✓] Deleted webhook ID: {webhook_id}")
    else:
        print(f"[✗] Failed to delete webhook ID {webhook_id}: {response.status_code}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/register_webhooks.py list")
        print("  python scripts/register_webhooks.py register <topic> <destination_url>")
        print("  python scripts/register_webhooks.py delete <webhook_id>")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "list":
        list_webhooks()
    elif cmd == "register" and len(sys.argv) >= 4:
        register_webhook(sys.argv[2], sys.argv[3])
    elif cmd == "delete" and len(sys.argv) >= 3:
        delete_webhook(int(sys.argv[2]))
    else:
        print("Invalid arguments.")
