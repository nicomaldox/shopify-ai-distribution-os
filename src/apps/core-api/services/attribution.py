import logging
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from dependencies.security import verify_signed_referral_token
from services.tracking import hash_visitor_ip

logger = logging.getLogger(__name__)

async def resolve_order_attribution(db: AsyncSession, order_payload: dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Multi-evidence Attribution Resolver.
    Determines which creator gets the commission for a given Shopify order.
    
    Priority:
    1. Coupon Code (Deterministic mapping to creator)
    2. Persistent Referral Token (From Shopify landing_site / ref parameter, HMAC verified)
    3. Last Eligible Click (Fallback, using hashed browser_ip)

    Returns: (creator_id, attribution_source)
    """
    
    # 1. Check for Coupon Code (Highest Priority)
    discount_codes = order_payload.get("discount_codes", [])
    if discount_codes:
        for discount in discount_codes:
            code = discount.get("code", "").upper()
            
            # Lookup which creator owns this code
            stmt = text("""
                SELECT creator_id 
                FROM affiliate_links 
                WHERE UPPER(coupon_code) = :code
            """)
            result = await db.execute(stmt, {"code": code})
            creator_id = result.scalar()
            
            if creator_id:
                logger.info(f"Attribution resolved via COUPON: {code} -> Creator {creator_id}")
                return str(creator_id), "COUPON"
                
    # 2. Check for Referral Token from landing_site or tags
    # Usually passed back by Shopify if we set a 'ref' cart attribute or tag
    tags = order_payload.get("tags", "")
    landing_site = order_payload.get("landing_site", "")
    
    # Simple extraction logic (can be expanded based on Shopify storefront setup)
    if "?ref=" in landing_site:
        token = landing_site.split("?ref=")[1].split("&")[0]
        slug = verify_signed_referral_token(token)
        
        if slug:
            stmt = text("""
                SELECT creator_id 
                FROM affiliate_links 
                WHERE slug = :slug
            """)
            result = await db.execute(stmt, {"slug": slug})
            creator_id = result.scalar()
            
            if creator_id:
                logger.info(f"Attribution resolved via SIGNED LINK: {slug} -> Creator {creator_id}")
                return str(creator_id), "LINK"
            
    # 3. Last Eligible Click (Fallback based on hashed IP matching)
    browser_ip = order_payload.get("browser_ip")
    if browser_ip:
        ip_hash = hash_visitor_ip(browser_ip)
        
        stmt = text("""
            SELECT al.creator_id 
            FROM click_events ce
            JOIN affiliate_links al ON ce.link_id = al.link_id
            WHERE ce.ip_hash = :ip_hash
            ORDER BY ce.clicked_at DESC
            LIMIT 1
        """)
        result = await db.execute(stmt, {"ip_hash": ip_hash})
        creator_id = result.scalar()
        
        if creator_id:
            logger.info(f"Attribution resolved via LAST CLICK (IP Match) -> Creator {creator_id}")
            return str(creator_id), "LAST_CLICK"

    # No attribution found
    logger.info("No attribution found for order.")
    return None, None
