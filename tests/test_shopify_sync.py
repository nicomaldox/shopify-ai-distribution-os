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

@pytest.mark.asyncio
async def test_sync_shopify_products():
    """Test mirroring Shopify products into PostgreSQL products table."""
    from services.shopify_sync import sync_shopify_products, sync_shopify_store

    mock_products = [
        {
            "id": 7769372393559,
            "title": "Luminous Hydrating Glow Serum",
            "variants": [{"price": "1280.00"}],
            "images": [{"src": "https://cdn.shopify.com/serum.jpg"}]
        },
        {
            "id": 7753120153687,
            "title": "test2",
            "variants": [{"price": "10000.00"}],
            "images": []
        }
    ]

    mock_db = AsyncMock()
    mock_db.execute.return_value = AsyncMock()

    with patch("services.shopify_sync.fetch_shopify_products", return_value=mock_products):
        result = await sync_shopify_products(mock_db)

    assert result["status"] == "SUCCESS"
    assert result["synced_count"] == 2
    assert result["products"][0]["product_id"] == "7769372393559"
    assert result["products"][0]["price"] == "1280.00"
    assert result["products"][0]["image_url"] == "https://cdn.shopify.com/serum.jpg"
    assert result["products"][1]["product_id"] == "7753120153687"
    assert result["products"][1]["title"] == "test2"
    assert result["products"][1]["image_url"] == ""

@pytest.mark.asyncio
async def test_sync_shopify_store():
    """Test unified store synchronization (both products and orders)."""
    from services.shopify_sync import sync_shopify_store

    mock_db = AsyncMock()
    with patch("services.shopify_sync.sync_shopify_products", return_value={"status": "SUCCESS", "synced_count": 4}), \
         patch("services.shopify_sync.sync_shopify_orders", return_value={"status": "SUCCESS", "new_orders": 0}):
        result = await sync_shopify_store(mock_db)

    assert result["status"] == "SUCCESS"
    assert result["products_sync"]["synced_count"] == 4
    assert result["orders_sync"]["new_orders"] == 0

