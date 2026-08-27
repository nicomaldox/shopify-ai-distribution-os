import pytest
from unittest.mock import AsyncMock
from decimal import Decimal
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/apps/core-api")))
from services.ledger import record_refund_reversal

@pytest.mark.asyncio
async def test_record_refund_reversal_full():
    """Test that a $100 full refund reverses exactly $20 if original order was $100."""
    mock_db = AsyncMock()
    
    # 1st query: get original order price and creator
    mock_order_res = AsyncMock()
    mock_order_res.fetchone.return_value = AsyncMock(total_price=Decimal("100.00"), attributed_creator_id="creator-abc")
    
    # 2nd query: get total original EARN
    mock_earn_res = AsyncMock()
    mock_earn_res.scalar.return_value = Decimal("20.0000")
    
    mock_db.execute.side_effect = [mock_order_res, mock_earn_res, AsyncMock()]
    
    await record_refund_reversal(mock_db, "order_123", "100.00")
    
    # Verify the reversal amount passed to the 3rd insert query
    insert_call = mock_db.execute.call_args_list[2]
    params = insert_call[0][1]
    
    assert params["amount"] == Decimal("-20.0000")

@pytest.mark.asyncio
async def test_record_refund_reversal_partial():
    """Test that a $50 partial refund reverses exactly $10 if original order was $100."""
    mock_db = AsyncMock()
    
    mock_order_res = AsyncMock()
    mock_order_res.fetchone.return_value = AsyncMock(total_price=Decimal("100.00"), attributed_creator_id="creator-abc")
    
    mock_earn_res = AsyncMock()
    mock_earn_res.scalar.return_value = Decimal("20.0000")
    
    mock_db.execute.side_effect = [mock_order_res, mock_earn_res, AsyncMock()]
    
    await record_refund_reversal(mock_db, "order_123", "50.00")
    
    insert_call = mock_db.execute.call_args_list[2]
    params = insert_call[0][1]
    assert params["amount"] == Decimal("-10.0000")

@pytest.mark.asyncio
async def test_record_refund_reversal_post_payout_carryover():
    """
    Test Scenario 5: Post-payout negative balance carryover.
    Ensures that a reversal is appended to the ledger even if it would 
    create a negative net balance for the creator (e.g. payout already occurred).
    """
    mock_db = AsyncMock()
    
    mock_order_res = AsyncMock()
    mock_order_res.fetchone.return_value = AsyncMock(total_price=Decimal("100.00"), attributed_creator_id="creator-abc")
    
    # Original EARN for the order was 20.00
    mock_earn_res = AsyncMock()
    mock_earn_res.scalar.return_value = Decimal("20.0000")
    
    mock_db.execute.side_effect = [mock_order_res, mock_earn_res, AsyncMock()]
    
    # Process full refund
    await record_refund_reversal(mock_db, "order_123", "100.00")
    
    insert_call = mock_db.execute.call_args_list[2]
    params = insert_call[0][1]
    
    # The reversal of -20.00 is unconditionally appended.
    # In a full system, `SUM(amount) FROM commission_ledger WHERE creator_id = X` 
    # would now simply be negative if a PAYOUT of 20.00 had already occurred.
    assert params["amount"] == Decimal("-20.0000")
    assert params["creator_id"] == "creator-abc"
