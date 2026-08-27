import pytest
from unittest.mock import AsyncMock, patch
from decimal import Decimal
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/apps/core-api")))
from services.ledger import record_commission_earn

@pytest.mark.asyncio
async def test_record_commission_earn():
    """Test that $100 order generates exact $20 EARN entry."""
    mock_db = AsyncMock()
    
    # We will test the default 20% commission
    order_id = "test_order_123"
    total_price = "100.00"
    creator_id = "creator-abc"
    
    await record_commission_earn(mock_db, order_id, total_price, creator_id)
    
    # Verify db.execute was called
    mock_db.execute.assert_called_once()
    
    # Verify the amount passed to the SQL statement is exactly Decimal("20.0000")
    call_args = mock_db.execute.call_args[0]
    params = call_args[1]
    
    assert params["creator_id"] == creator_id
    assert params["order_id"] == order_id
    assert params["amount"] == Decimal("20.0000")
