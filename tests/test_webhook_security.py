import pytest
import hmac
import hashlib
import base64
from fastapi.testclient import TestClient
import sys
import os

# Ensure the app can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/apps/core-api")))
os.environ["SHOPIFY_WEBHOOK_SECRET"] = "test_secret"

from main import app

client = TestClient(app)

def sign_payload(payload: str, secret: str = "test_secret") -> str:
    digest = hmac.new(
        secret.encode("utf-8"), 
        payload.encode("utf-8"), 
        hashlib.sha256
    ).digest()
    return base64.b64encode(digest).decode("utf-8")

def test_webhook_missing_hmac_header():
    response = client.post("/webhooks/shopify/", json={"id": 123})
    assert response.status_code == 401
    assert "Missing" in response.json()["detail"]

def test_webhook_invalid_hmac_signature():
    payload = '{"id": 123}'
    headers = {
        "X-Shopify-Hmac-SHA256": "invalid_signature",
        "X-Shopify-Topic": "orders/paid",
        "X-Shopify-Webhook-Id": "webhook_123",
        "X-Shopify-Shop-Domain": "test.myshopify.com"
    }
    response = client.post("/webhooks/shopify/", content=payload, headers=headers)
    assert response.status_code == 401
    assert "Invalid HMAC signature" in response.json()["detail"]

def test_webhook_valid_hmac_signature():
    # Note: we won't fully test DB insertion here without mocking the DB, 
    # but we can test if it gets past the security dependency.
    # Without mocking the DB, the route will try to connect to postgres and fail or succeed.
    # To keep it isolated to security, we can just assert it doesn't return 401.
    payload = '{"id": 123}'
    signature = sign_payload(payload)
    headers = {
        "X-Shopify-Hmac-SHA256": signature,
        "X-Shopify-Topic": "orders/paid",
        "X-Shopify-Webhook-Id": "webhook_123",
        "X-Shopify-Shop-Domain": "test.myshopify.com"
    }
    
    # We expect this to fail due to DB connection or similar, but NOT 401
    response = client.post("/webhooks/shopify/", content=payload, headers=headers)
    assert response.status_code != 401
