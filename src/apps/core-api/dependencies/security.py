import os
import hmac
import hashlib
import base64
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

SHOPIFY_WEBHOOK_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET", "")

async def verify_shopify_webhook(request: Request) -> bytes:
    """
    Dependency to verify Shopify HMAC-SHA256 signature using constant-time comparison.
    Returns the raw body bytes if valid.
    """
    hmac_header = request.headers.get("X-Shopify-Hmac-SHA256")
    if not hmac_header:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, 
            detail="Missing X-Shopify-Hmac-SHA256 header"
        )

    # Read raw body before FastAPI parses it as JSON
    raw_body = await request.body()
    
    if not SHOPIFY_WEBHOOK_SECRET:
        # In a real scenario, this might log an error. We allow it to fail securely.
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    digest = hmac.new(
        SHOPIFY_WEBHOOK_SECRET.encode("utf-8"), 
        raw_body, 
        hashlib.sha256
    ).digest()
    
    computed_hmac = base64.b64encode(digest).decode("utf-8")
    
    if not hmac.compare_digest(computed_hmac, hmac_header):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, 
            detail="Invalid HMAC signature"
        )
        
    return raw_body

JWT_SECRET = os.getenv("JWT_SECRET", "dev_jwt_secret_change_me")

def generate_signed_referral_token(slug: str) -> str:
    """Generates an HMAC-signed referral token."""
    signature = hmac.new(
        JWT_SECRET.encode("utf-8"), 
        slug.encode("utf-8"), 
        hashlib.sha256
    ).hexdigest()
    return f"{slug}.{signature}"

def verify_signed_referral_token(token: str) -> str | None:
    """Verifies and extracts the slug from a signed token. Returns None if invalid."""
    parts = token.split(".")
    if len(parts) != 2:
        return None
        
    slug, signature = parts
    expected = hmac.new(
        JWT_SECRET.encode("utf-8"), 
        slug.encode("utf-8"), 
        hashlib.sha256
    ).hexdigest()
    
    if hmac.compare_digest(expected, signature):
        return slug
    return None
