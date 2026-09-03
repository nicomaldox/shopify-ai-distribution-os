import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/apps/core-api")))
from routers.redirects import is_safe_redirect_url
from services.tracking import hash_visitor_ip
from dependencies.security import generate_signed_referral_token, verify_signed_referral_token

def test_is_safe_redirect_url_domain_allowlist():
    # Set the env var expected by the router
    os.environ["SHOPIFY_SHOP_DOMAIN"] = "test.myshopify.com"
    
    assert is_safe_redirect_url("https://test.myshopify.com/") is True
    assert is_safe_redirect_url("https://test.myshopify.com/products/1") is True
    
    # Should reject other domains
    assert is_safe_redirect_url("https://evil.com/") is False
    assert is_safe_redirect_url("https://test.myshopify.com.evil.com/") is False

def test_is_safe_redirect_url_ssrf():
    os.environ["SHOPIFY_SHOP_DOMAIN"] = "test.myshopify.com"
    # Even if they spoof the domain string, if it resolves to a private IP, it's blocked.
    # We will test common private IP blocks by passing them as the host.
    assert is_safe_redirect_url("http://127.0.0.1/") is False
    assert is_safe_redirect_url("http://10.0.0.1/") is False
    assert is_safe_redirect_url("http://169.254.169.254/") is False # Cloud Metadata
    assert is_safe_redirect_url("http://localhost/") is False

def test_ip_hashing():
    ip1 = "192.168.1.1"
    ip2 = "192.168.1.2"
    
    hash1 = hash_visitor_ip(ip1)
    hash2 = hash_visitor_ip(ip2)
    
    # Must be deterministic
    assert hash_visitor_ip(ip1) == hash1
    # Must be distinct
    assert hash1 != hash2
    # Must not contain the raw IP
    assert ip1 not in hash1

def test_signed_referral_tokens():
    slug = "alex"
    token = generate_signed_referral_token(slug)
    
    assert "." in token
    
    # Verify valid token
    extracted = verify_signed_referral_token(token)
    assert extracted == slug
    
    # Verify invalid token
    assert verify_signed_referral_token(f"{slug}.invalid_sig") is None
    assert verify_signed_referral_token("just_a_slug") is None

from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException, Request
from routers.redirects import redirect_gateway

@pytest.mark.asyncio
async def test_redirect_gateway_unapproved_slug():
    """Verify that visiting an unapproved or unknown slug triggers HTTP 400 Bad Request."""
    mock_request = AsyncMock(spec=Request)
    mock_request.query_params.get.return_value = None
    
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.fetchone.return_value = None
    mock_db.execute.return_value = mock_res
    
    with pytest.raises(HTTPException) as exc_info:
        await redirect_gateway(slug="malicious-link", request=mock_request, db=mock_db)
        
    assert exc_info.value.status_code == 400
    assert "Open redirect defense" in exc_info.value.detail
    assert "malicious-link" in exc_info.value.detail

@pytest.mark.asyncio
async def test_redirect_gateway_unauthorized_dest_param():
    """Verify that attempts to override destination to an unauthorized domain trigger HTTP 400 Bad Request."""
    mock_request = AsyncMock(spec=Request)
    mock_request.query_params.get.side_effect = lambda k, default=None: {
        "dest": "https://evil.com"
    }.get(k, default)
    
    mock_db = AsyncMock()
    
    with pytest.raises(HTTPException) as exc_info:
        await redirect_gateway(slug="alex-tech", request=mock_request, db=mock_db)
        
    assert exc_info.value.status_code == 400
    assert "not an authorized Shopify domain" in exc_info.value.detail

@pytest.mark.asyncio
async def test_redirect_gateway_ssrf_dest_param():
    """Verify that destination parameters resolving to private IPs/cloud metadata trigger HTTP 400 Bad Request."""
    mock_request = AsyncMock(spec=Request)
    mock_request.query_params.get.side_effect = lambda k, default=None: {
        "dest": "http://169.254.169.254"
    }.get(k, default)
    
    mock_db = AsyncMock()
    
    with pytest.raises(HTTPException) as exc_info:
        await redirect_gateway(slug="alex-tech", request=mock_request, db=mock_db)
        
    assert exc_info.value.status_code == 400

@pytest.mark.asyncio
async def test_redirect_gateway_approved_slug_success():
    """Verify that an approved slug logs the click and returns HTTP 302 to the Shopify store."""
    os.environ["SHOPIFY_SHOP_DOMAIN"] = "0efjx4-fp.myshopify.com"
    
    mock_request = AsyncMock(spec=Request)
    mock_request.query_params.get.return_value = None
    mock_request.client.host = "192.168.1.50"
    mock_request.headers.get.return_value = "Mozilla/5.0"
    
    mock_db = AsyncMock()
    mock_link = MagicMock()
    mock_link.link_id = "link-uuid-123"
    mock_link.creator_id = "creator-uuid-456"
    
    mock_lookup_res = MagicMock()
    mock_lookup_res.fetchone.return_value = mock_link
    
    mock_insert_res = MagicMock()
    mock_insert_res.scalar.return_value = "click-uuid-789"
    
    mock_db.execute.side_effect = [mock_lookup_res, mock_insert_res]
    
    response = await redirect_gateway(slug="alex-tech", request=mock_request, db=mock_db)
    
    assert response.status_code == 302
    assert "https://0efjx4-fp.myshopify.com/?ref=" in response.headers["location"]

