import os
import hmac
import hashlib
import base64
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

def get_shopify_candidate_secrets() -> list[str]:
    """Collect and sanitize all potential Shopify webhook signing secrets."""
    secrets = []
    for var in ("SHOPIFY_WEBHOOK_SECRET", "SHOPIFY_APP_SECRET"):
        val = os.getenv(var, "").strip()
        if val and val not in secrets:
            secrets.append(val)
    return secrets

async def verify_shopify_webhook(request: Request) -> bytes:
    """
    Dependency to verify Shopify HMAC-SHA256 signature using constant-time comparison.
    Supports candidate secrets (Notification Secret vs App API Secret) and strips CRLF artifacts.
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
    candidate_secrets = get_shopify_candidate_secrets()
    
    # Check if explicit developer bypass is enabled
    bypass_hmac = os.getenv("BYPASS_WEBHOOK_HMAC", "false").lower() in ("true", "1")
    if bypass_hmac:
        import logging
        logging.getLogger(__name__).warning("BYPASS_WEBHOOK_HMAC is enabled: Skipping HMAC signature check.")
        return raw_body

    if not candidate_secrets:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    valid = False
    for secret in candidate_secrets:
        digest = hmac.new(
            secret.encode("utf-8"), 
            raw_body, 
            hashlib.sha256
        ).digest()
        computed_hmac = base64.b64encode(digest).decode("utf-8")
        if hmac.compare_digest(computed_hmac, hmac_header):
            valid = True
            break
    
    if not valid:
        import logging
        logging.getLogger(__name__).warning(
            f"Shopify HMAC Mismatch! Header: '{hmac_header}' | Candidates evaluated: {len(candidate_secrets)} | Body length: {len(raw_body)}"
        )
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
