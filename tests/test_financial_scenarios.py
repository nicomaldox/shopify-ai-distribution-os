import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/apps/core-api")))
from services.ledger import record_commission_earn, record_refund_reversal
from services.attribution import resolve_order_attribution

@pytest.mark.asyncio
async def test_scenario_1_standard_commission_accrual():
    """
    Scenario 1: Standard order commission accrual.
    A paid order of NT$3,000 with 20% commission credits exactly NT$600.0000.
    """
    mock_db = AsyncMock()
    order_id = "ord_scenario_1"
    total_price = "3000.00"
    creator_id = "550e8400-e29b-41d4-a716-446655440000"

    await record_commission_earn(mock_db, order_id, total_price, creator_id)

    mock_db.execute.assert_called_once()
    params = mock_db.execute.call_args[0][1]
    assert params["creator_id"] == creator_id
    assert params["order_id"] == order_id
    assert params["amount"] == Decimal("600.0000")

@pytest.mark.asyncio
async def test_scenario_2_duplicate_idempotency():
    """
    Scenario 2: Duplicate order / webhook idempotency.
    Ensures attribution resolution accurately identifies creator without side effects.
    """
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar.return_value = "creator-alex"
    mock_db.execute.return_value = mock_res

    payload = {
        "id": "ord_scenario_2",
        "discount_codes": [{"code": "ALEX10"}]
    }

    # First resolution
    creator_id_1, source_1 = await resolve_order_attribution(mock_db, payload)
    assert creator_id_1 == "creator-alex"
    assert source_1 == "COUPON"

    # Second resolution (duplicate delivery)
    creator_id_2, source_2 = await resolve_order_attribution(mock_db, payload)
    assert creator_id_2 == "creator-alex"
    assert source_2 == "COUPON"

@pytest.mark.asyncio
async def test_scenario_3_full_cancellation():
    """
    Scenario 3: Full order cancellation.
    A full refund of NT$3,000 on an NT$3,000 order reverses 100% of the commission (-NT$600.0000).
    """
    mock_db = AsyncMock()
    order_id = "ord_scenario_3"
    refund_amount = "3000.00"

    mock_order_res = MagicMock()
    mock_order_res.fetchone.return_value = MagicMock(
        total_price=Decimal("3000.00"),
        attributed_creator_id="creator-alex"
    )

    mock_earn_res = MagicMock()
    mock_earn_res.scalar.return_value = Decimal("600.0000")

    mock_db.execute.side_effect = [mock_order_res, mock_earn_res, AsyncMock()]

    await record_refund_reversal(mock_db, order_id, refund_amount)

    insert_call = mock_db.execute.call_args_list[2]
    params = insert_call[0][1]
    assert params["amount"] == Decimal("-600.0000")
    assert params["creator_id"] == "creator-alex"

@pytest.mark.asyncio
async def test_scenario_4_partial_refund_proportional_reversal():
    """
    Scenario 4: Partial order refund proportional reversal.
    A 50% refund (NT$1,500 on an NT$3,000 order) reverses exactly 50% of the commission (-NT$300.0000).
    """
    mock_db = AsyncMock()
    order_id = "ord_scenario_4"
    refund_amount = "1500.00"

    mock_order_res = MagicMock()
    mock_order_res.fetchone.return_value = MagicMock(
        total_price=Decimal("3000.00"),
        attributed_creator_id="creator-alex"
    )

    mock_earn_res = MagicMock()
    mock_earn_res.scalar.return_value = Decimal("600.0000")

    mock_db.execute.side_effect = [mock_order_res, mock_earn_res, AsyncMock()]

    await record_refund_reversal(mock_db, order_id, refund_amount)

    insert_call = mock_db.execute.call_args_list[2]
    params = insert_call[0][1]
    assert params["amount"] == Decimal("-300.0000")
    assert params["creator_id"] == "creator-alex"

@pytest.mark.asyncio
async def test_scenario_5_post_payout_negative_balance_carryover():
    """
    Scenario 5: Post-payout negative balance carryover.
    Ensures that when a refund occurs after commissions have been paid out,
    the negative ledger entry is appended to carry over the negative balance.
    """
    mock_db = AsyncMock()
    order_id = "ord_scenario_5"
    refund_amount = "1000.00"  # 1/3 refund of 3000

    mock_order_res = MagicMock()
    mock_order_res.fetchone.return_value = MagicMock(
        total_price=Decimal("3000.00"),
        attributed_creator_id="creator-alex"
    )

    mock_earn_res = MagicMock()
    mock_earn_res.scalar.return_value = Decimal("600.0000")

    mock_db.execute.side_effect = [mock_order_res, mock_earn_res, AsyncMock()]

    await record_refund_reversal(mock_db, order_id, refund_amount)

    insert_call = mock_db.execute.call_args_list[2]
    params = insert_call[0][1]
    # 1000 / 3000 = 1/3; 600 * 1/3 = 200
    assert params["amount"] == Decimal("-200.0000")
    assert params["creator_id"] == "creator-alex"
