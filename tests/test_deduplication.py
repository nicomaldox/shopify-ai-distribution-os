import pytest
from unittest.mock import AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/apps/core-api")))
from routers.webhooks import shopify_webhook_receiver
from sqlalchemy.exc import IntegrityError
from fastapi import Request

@pytest.mark.asyncio
async def test_webhook_idempotency_duplicate_catch():
    """
    Test that an IntegrityError (duplicate webhook ID) is caught and gracefully ignored (HTTP 200).
    """
    # Mock request
    mock_request = AsyncMock(spec=Request)
    mock_request.headers.get.side_effect = lambda k: {
        "X-Shopify-Webhook-Id": "duplicate_id_123",
        "X-Shopify-Topic": "orders/paid",
        "X-Shopify-Shop-Domain": "test.myshopify.com"
    }.get(k)
    
    # Mock DB session to raise IntegrityError on execute
    mock_db = AsyncMock()
    # Create an IntegrityError instance
    mock_db.execute.side_effect = IntegrityError("statement", "params", "orig")
    
    # Call the router function directly
    raw_body = b'{"id": 123}'
    
    response = await shopify_webhook_receiver(request=mock_request, raw_body=raw_body, db=mock_db)
    
    # Should safely return 200 OK to acknowledge receipt
    assert response == {"status": "ok", "message": "Duplicate ignored"}
    
    # Assert rollback was called
    mock_db.rollback.assert_called_once()
