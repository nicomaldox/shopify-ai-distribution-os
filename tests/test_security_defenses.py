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
