import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/apps/core-api")))
from services.shopify_sync import sync_shopify_orders

@pytest.mark.asyncio
async def test_sync_shopify_orders_new_attributed_order():
    """Test syncing a new paid order attributed via discount code."""
    mock_orders = [
        {
            "id": 99887766,
            "total_price": "3000.00",
            "currency": "TWD",
            "financial_status": "paid",
            "discount_codes": [{"code": "ALEX10"}],
            "line_items": [
                {
                    "id": 112233,
                    "product_id": 445566,
                    "title": "Shopify AI License",
                    "quantity": 1,
                    "price": "3000.00"
                }
            ],
            "refunds": []
        }
    ]

    mock_db = AsyncMock()
    # 1. Check existing order -> returns None (new order)
    mock_check_res = MagicMock()
    mock_check_res.fetchone.return_value = None

    # 2. Coupon lookup in resolve_order_attribution -> returns creator-alex
    mock_coupon_res = MagicMock()
    mock_coupon_res.scalar.return_value = "creator-alex"

    mock_db.execute.side_effect = [mock_check_res, mock_coupon_res, AsyncMock(), AsyncMock(), AsyncMock()]

    with patch("services.shopify_sync.fetch_shopify_orders", return_value=mock_orders):
        result = await sync_shopify_orders(mock_db)

    assert result["status"] == "SUCCESS"
    assert result["fetched_count"] == 1
    assert result["new_orders"] == 1
    assert result["details"][0]["action"] == "EARN_RECORDED"
    assert result["details"][0]["creator_id"] == "creator-alex"

@pytest.mark.asyncio
async def test_sync_shopify_orders_duplicate_order_skipped():
    """Test that existing order is not double-processed."""
    mock_orders = [
        {
            "id": 99887766,
            "total_price": "3000.00",
            "currency": "TWD",
            "financial_status": "paid",
            "refunds": []
        }
    ]

    mock_db = AsyncMock()
    mock_check_res = MagicMock()
    # Order already exists with status 'paid'
    mock_check_res.fetchone.return_value = MagicMock(order_id="99887766", financial_status="paid")
    mock_db.execute.return_value = mock_check_res

    with patch("services.shopify_sync.fetch_shopify_orders", return_value=mock_orders):
        result = await sync_shopify_orders(mock_db)

    assert result["status"] == "SUCCESS"
    assert result["fetched_count"] == 1
    assert result["new_orders"] == 0
