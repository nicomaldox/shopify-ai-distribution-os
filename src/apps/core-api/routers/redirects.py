import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database.connection import get_db_session
from services.tracking import hash_visitor_ip
from dependencies.security import generate_signed_referral_token
import os
import socket
import ipaddress
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Tracking"])

SHOPIFY_SHOP_DOMAIN = os.getenv("SHOPIFY_SHOP_DOMAIN", "your-store.myshopify.com")

def is_safe_redirect_url(url: str) -> bool:
    """Validates domain allowlist and prevents SSRF to private IPs."""
    try:
        parsed = urlparse(url)
        domain = parsed.hostname
        if not domain:
            return False
            
        # Domain Allowlist Check
        if domain != SHOPIFY_SHOP_DOMAIN and not domain.endswith(".myshopify.com"):
            return False
            
        # SSRF Private IP check
        ip_addr = socket.gethostbyname(domain)
        ip = ipaddress.ip_address(ip_addr)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
            
        return True
    except Exception:
        return False

@router.get("/r/{slug}")
async def redirect_gateway(
    slug: str, 
    request: Request, 
    db: AsyncSession = Depends(get_db_session)
):
    """
    High-performance public redirect gateway.
    Logs the click securely, hashes the IP, and redirects to the Shopify store.
    """
    # 1. Lookup the slug in the affiliate_links table
    stmt = text("""
        SELECT link_id, creator_id 
        FROM affiliate_links 
        WHERE slug = :slug
    """)
    result = await db.execute(stmt, {"slug": slug})
    link_record = result.fetchone()

    if not link_record:
        # Prevent open-redirect or dead links: safely redirect to home page
        return RedirectResponse(url=f"https://{SHOPIFY_SHOP_DOMAIN}/", status_code=302)

    # 2. Extract visitor details securely
    raw_ip = request.client.host if request.client else "unknown"
    ip_hash = hash_visitor_ip(raw_ip)
    user_agent = request.headers.get("user-agent", "")
    
    # Extract UTMs if present
    utm_source = request.query_params.get("utm_source", "ai_distribution_os")
    utm_medium = request.query_params.get("utm_medium", "creator_link")
    utm_campaign = request.query_params.get("utm_campaign", slug)

    # 3. Log the click event (non-blocking in a real production system, but awaited here for simplicity)
    try:
        insert_click = text("""
            INSERT INTO click_events (link_id, ip_hash, user_agent, utm_source, utm_medium, utm_campaign)
            VALUES (:link_id, :ip_hash, :user_agent, :utm_source, :utm_medium, :utm_campaign)
            RETURNING click_id
        """)
        click_res = await db.execute(insert_click, {
            "link_id": link_record.link_id,
            "ip_hash": ip_hash,
            "user_agent": user_agent[:255], # Truncate if malicious/too long
            "utm_source": utm_source,
            "utm_medium": utm_medium,
            "utm_campaign": utm_campaign
        })
        click_id = click_res.scalar()
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to log click for slug {slug}: {str(e)}")
        # Continue the redirect even if logging fails (Availability > Logging)

    # 4. Redirect to Shopify with the referral identifier
    # Generate a cryptographically signed token to prevent spoofing
    signed_token = generate_signed_referral_token(slug)
    destination_url = f"https://{SHOPIFY_SHOP_DOMAIN}/?ref={signed_token}"
    
    if not is_safe_redirect_url(destination_url):
        logger.error(f"Unsafe redirect URL detected: {destination_url}")
        raise HTTPException(status_code=400, detail="Invalid redirect destination")
    
    return RedirectResponse(url=destination_url, status_code=302)
