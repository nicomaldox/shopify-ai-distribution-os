import hashlib
import os

SESSION_SALT = os.getenv("SESSION_SALT", "dev_session_salt_change_me")

def hash_visitor_ip(ip_address: str) -> str:
    """
    Hashes the raw IP address with a session salt to protect PII.
    Complies with GDPR/CCPA by ensuring raw IPs are never stored.
    """
    if not ip_address:
        ip_address = "unknown_ip"
    
    # Hash using SHA-256 with salt
    return hashlib.sha256(f"{ip_address}:{SESSION_SALT}".encode("utf-8")).hexdigest()
