import pytest
from unittest.mock import AsyncMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/apps/core-api")))
from services.attribution import resolve_order_attribution
from dependencies.security import generate_signed_referral_token

@pytest.mark.asyncio
async def test_attribution_priority_1_coupon():
    """Test that Coupon Code takes highest priority."""
    mock_db = AsyncMock()
    # Mock the DB returning creator_id 'creator-123' for the coupon lookup
    mock_db.execute.return_value.scalar.return_value = "creator-123"
    
    order_payload = {
        "discount_codes": [{"code": "ALEX10"}],
        "landing_site": "/?ref=other_creator_token" # This should be ignored
    }
    
    creator_id, source = await resolve_order_attribution(mock_db, order_payload)
    
    assert creator_id == "creator-123"
    assert source == "COUPON"

@pytest.mark.asyncio
async def test_attribution_priority_2_signed_link():
    """Test that Signed Token takes priority if no coupon."""
    mock_db = AsyncMock()
    mock_db.execute.return_value.scalar.return_value = "creator-456"
    
    # Generate valid signed token for slug 'sam'
    valid_token = generate_signed_referral_token("sam")
    
    order_payload = {
        "landing_site": f"/?ref={valid_token}"
    }
    
    creator_id, source = await resolve_order_attribution(mock_db, order_payload)
    
    assert creator_id == "creator-456"
    assert source == "LINK"

@pytest.mark.asyncio
async def test_attribution_priority_3_last_click():
    """Test Last Click fallback using hashed IP."""
    mock_db = AsyncMock()
    mock_db.execute.return_value.scalar.return_value = "creator-789"
    
    order_payload = {
        "browser_ip": "192.168.1.1"
    }
    
    creator_id, source = await resolve_order_attribution(mock_db, order_payload)
    
    assert creator_id == "creator-789"
    assert source == "LAST_CLICK"
