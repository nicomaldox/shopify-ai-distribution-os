import os
import logging
from decimal import Decimal, ROUND_HALF_UP
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from services.attribution import resolve_order_attribution
from services.ledger import record_commission_earn, record_refund_reversal

logger = logging.getLogger(__name__)

SHOPIFY_SHOP_DOMAIN = os.getenv("SHOPIFY_SHOP_DOMAIN", "0efjx4-fp.myshopify.com")
SHOPIFY_ADMIN_API_ACCESS_TOKEN = os.getenv("SHOPIFY_ADMIN_API_ACCESS_TOKEN", "")

async def fetch_shopify_orders(limit: int = 50) -> list[dict]:
    """
    Fetches recent orders directly from Shopify Admin REST API.
    Does not require any inbound webhook, domain, or public tunnel.
    """
    token = os.getenv("SHOPIFY_ADMIN_API_ACCESS_TOKEN", SHOPIFY_ADMIN_API_ACCESS_TOKEN).strip()
    shop = os.getenv("SHOPIFY_SHOP_DOMAIN", SHOPIFY_SHOP_DOMAIN).strip()
    
    if not token or not shop:
        logger.warning("Shopify credentials not configured; skipping sync.")
        return []

    url = f"https://{shop}/admin/api/2024-01/orders.json"
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }
    params = {
        "status": "any",
        "limit": limit
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("orders", [])
            else:
                logger.error(f"Shopify Admin API error: {response.status_code} - {response.text}")
                return []
    except Exception as e:
        logger.error(f"Failed to fetch orders from Shopify Admin API: {e}")
        return []

async def sync_shopify_orders(db: AsyncSession, limit: int = 50) -> dict:
    """
    Synchronizes Shopify orders and refunds idempotently with the local database.
    Resolves creator attribution and updates the append-only commission ledger.
    """
    raw_orders = await fetch_shopify_orders(limit=limit)
    if not raw_orders:
        return {
            "status": "COMPLETED",
            "message": "No orders fetched or credentials missing",
            "fetched_count": 0,
            "new_orders": 0,
            "refunds_processed": 0
        }

    new_orders_count = 0
    refunds_processed_count = 0
    details = []

    for order in raw_orders:
        order_id = str(order.get("id"))
        total_price = str(order.get("total_price", "0.0"))
        currency = str(order.get("currency", "TWD"))
        financial_status = order.get("financial_status")

        try:
            # 1. Check if the order already exists in our local orders table
            stmt_check = text("SELECT order_id, financial_status FROM orders WHERE order_id = :order_id")
            res_check = await db.execute(stmt_check, {"order_id": order_id})
            existing_order = res_check.fetchone()

            if not existing_order:
                # Resolve creator attribution for the new order
                creator_id, attribution_source = await resolve_order_attribution(db, order)

                # Insert into orders table
                stmt_insert = text("""
                    INSERT INTO orders (order_id, total_price, currency, financial_status, attributed_creator_id, attribution_source)
                    VALUES (:order_id, :total_price, :currency, :financial_status, :creator_id, :attribution_source)
                    ON CONFLICT (order_id) DO NOTHING
                """)
                await db.execute(stmt_insert, {
                    "order_id": order_id,
                    "total_price": total_price,
                    "currency": currency,
                    "financial_status": financial_status,
                    "creator_id": creator_id,
                    "attribution_source": attribution_source
                })

                # Insert line items
                for item in order.get("line_items", []):
                    item_id = str(item.get("id"))
                    product_id = str(item.get("product_id"))
                    title = item.get("title", "")
                    quantity = int(item.get("quantity", 1))
                    price = str(item.get("price", "0.0"))

                    stmt_item = text("""
                        INSERT INTO order_items (item_id, order_id, product_id, title, quantity, price)
                        VALUES (:item_id, :order_id, :product_id, :title, :quantity, :price)
                        ON CONFLICT (item_id) DO NOTHING
                    """)
                    await db.execute(stmt_item, {
                        "item_id": item_id,
                        "order_id": order_id,
                        "product_id": product_id,
                        "title": title,
                        "quantity": quantity,
                        "price": price
                    })

                # Record Commission EARN if attributed and paid
                if creator_id and financial_status in ("paid", "partially_refunded", "refunded"):
                    await record_commission_earn(db, order_id, total_price, creator_id)

                new_orders_count += 1
                details.append({
                    "order_id": order_id,
                    "action": "EARN_RECORDED" if creator_id else "UNATTRIBUTED_ORDER",
                    "total_price": total_price,
                    "creator_id": creator_id
                })
            else:
                # Update financial status if changed (e.g., from paid to refunded)
                if existing_order.financial_status != financial_status:
                    stmt_update = text("UPDATE orders SET financial_status = :status WHERE order_id = :order_id")
                    await db.execute(stmt_update, {"status": financial_status, "order_id": order_id})

            # 2. Process any refunds present on this order
            refunds = order.get("refunds", [])
            if refunds:
                total_refund_amount = Decimal("0")
                for ref in refunds:
                    # Sum successful refund transactions
                    tx_sum = sum(
                        (Decimal(str(tx.get("amount", "0"))) for tx in ref.get("transactions", []) if tx.get("status") == "success"),
                        start=Decimal("0")
                    )
                    if tx_sum > Decimal("0"):
                        total_refund_amount += tx_sum
                    else:
                        # Fallback to refund_line_items subtotal
                        line_sum = sum(
                            (Decimal(str(li.get("subtotal", "0"))) for li in ref.get("refund_line_items", [])),
                            start=Decimal("0")
                        )
                        total_refund_amount += line_sum

                if total_refund_amount > Decimal("0"):
                    # Calculate how much reversal is expected vs already recorded
                    # First check original earn on this order
                    stmt_earn = text("SELECT amount FROM commission_ledger WHERE order_id = :order_id AND transaction_type = 'EARN'")
                    res_earn = await db.execute(stmt_earn, {"order_id": order_id})
                    earn_record = res_earn.scalar()

                    if earn_record:
                        orig_earn_dec = Decimal(str(earn_record))
                        orig_price_dec = Decimal(str(total_price))
                        if orig_price_dec > Decimal("0"):
                            expected_total_rev = (orig_earn_dec * (total_refund_amount / orig_price_dec)).quantize(Decimal("0.0000"), rounding=ROUND_HALF_UP)
                            
                            # Check existing reversals in ledger
                            stmt_rev_sum = text("""
                                SELECT COALESCE(ABS(SUM(amount)), 0) 
                                FROM commission_ledger 
                                WHERE order_id = :order_id AND transaction_type = 'REVERSAL'
                            """)
                            res_rev_sum = await db.execute(stmt_rev_sum, {"order_id": order_id})
                            already_reversed = Decimal(str(res_rev_sum.scalar() or "0"))

                            # If there is an unreversed delta, record reversal for the difference
                            delta_reversal = expected_total_rev - already_reversed
                            if delta_reversal > Decimal("0.0001"):
                                # Calculate the corresponding refund amount delta
                                refund_delta = (delta_reversal / orig_earn_dec * orig_price_dec).quantize(Decimal("0.0000"), rounding=ROUND_HALF_UP)
                                await record_refund_reversal(db, order_id, str(refund_delta))
                                refunds_processed_count += 1
                                details.append({
                                    "order_id": order_id,
                                    "action": "REVERSAL_RECORDED",
                                    "refund_amount": str(refund_delta)
                                })

            await db.commit()

        except Exception as e:
            await db.rollback()
            logger.error(f"Error synchronizing order {order_id}: {e}")

    return {
        "status": "SUCCESS",
        "fetched_count": len(raw_orders),
        "new_orders": new_orders_count,
        "refunds_processed": refunds_processed_count,
        "details": details
    }
