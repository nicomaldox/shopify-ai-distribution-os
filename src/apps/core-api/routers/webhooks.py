import json
import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from dependencies.security import verify_shopify_webhook
from database.connection import get_db_session
from services.attribution import resolve_order_attribution
from services.ledger import record_commission_earn, record_refund_reversal
from decimal import Decimal

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/shopify", tags=["Webhooks"])

@router.post("/")
async def shopify_webhook_receiver(
    request: Request,
    raw_body: bytes = Depends(verify_shopify_webhook),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generic webhook receiver for Shopify events.
    Enforces idempotency using X-Shopify-Webhook-Id in the webhook_inbox table.
    """
    webhook_id = request.headers.get("X-Shopify-Webhook-Id")
    topic = request.headers.get("X-Shopify-Topic")
    shop_domain = request.headers.get("X-Shopify-Shop-Domain")

    if not webhook_id or not topic:
        raise HTTPException(status_code=400, detail="Missing essential webhook headers")

    # 1. Idempotency Check & Lock
    # We attempt to insert into webhook_inbox. If it fails due to UNIQUE constraint, it's a duplicate.
    try:
        stmt = text("""
            INSERT INTO webhook_inbox (webhook_id, topic, shop_domain)
            VALUES (:webhook_id, :topic, :shop_domain)
        """)
        await db.execute(stmt, {"webhook_id": webhook_id, "topic": topic, "shop_domain": shop_domain})
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # Log and safely return 200 to acknowledge receipt without re-processing (Idempotency)
        logger.info(f"Duplicate webhook detected and skipped: {webhook_id}")
        return {"status": "ok", "message": "Duplicate ignored"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error saving webhook_inbox: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    # 2. Parse payload safely now that HMAC is verified and it's a new event
    payload = json.loads(raw_body.decode("utf-8"))

    # 3. Route by Topic (Outbox pattern triggers will be added here later)
    if topic == "orders/paid":
        logger.info(f"Processing orders/paid for {shop_domain}")
        order_id = str(payload.get("id"))
        total_price = payload.get("total_price", "0.0")
        currency = payload.get("currency", "TWD")
        financial_status = payload.get("financial_status")
        
        # Resolve attribution
        creator_id, attribution_source = await resolve_order_attribution(db, payload)
        
        # Insert into orders
        try:
            stmt = text("""
                INSERT INTO orders (order_id, total_price, currency, financial_status, attributed_creator_id, attribution_source)
                VALUES (:order_id, :total_price, :currency, :financial_status, :creator_id, :attribution_source)
                ON CONFLICT (order_id) DO NOTHING
            """)
            await db.execute(stmt, {
                "order_id": order_id,
                "total_price": total_price,
                "currency": currency,
                "financial_status": financial_status,
                "creator_id": creator_id,
                "attribution_source": attribution_source
            })
            
            # Insert items
            line_items = payload.get("line_items", [])
            for item in line_items:
                item_id = str(item.get("id"))
                product_id = str(item.get("product_id"))
                title = item.get("title")
                quantity = item.get("quantity", 1)
                price = item.get("price", "0.0")
                
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
            
            # Record Commission Earn in the Ledger atomically
            if creator_id:
                await record_commission_earn(db, order_id, total_price, creator_id)
                
            await db.commit()

                
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to process orders/paid: {e}")
            raise HTTPException(status_code=500, detail="Internal processing error")
            
    elif topic == "refunds/create":
        logger.info(f"Processing refunds/create for {shop_domain}")
        raw_order_id = payload.get("order_id")
        if raw_order_id is None:
            logger.warning("No order_id in refunds/create payload. Skipping.")
            return {"status": "ok", "message": "Skipped due to missing order_id"}
        order_id = str(raw_order_id)
        
        # Safely extract refund amount from transactions using precise Decimal math
        transactions = payload.get("transactions", [])
        refund_amount = sum((Decimal(str(tx.get("amount", "0"))) for tx in transactions if tx.get("status") == "success"), start=Decimal("0"))
        
        if refund_amount > Decimal("0"):
            try:
                await record_refund_reversal(db, order_id, str(refund_amount))
                await db.commit()
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to process refunds/create: {e}")
                raise HTTPException(status_code=500, detail="Internal processing error")
    elif topic == "products/update":
        logger.info(f"Processing products/update for {shop_domain}")
        product_id = str(payload.get("id"))
        title = payload.get("title", "")
        # Get price from first variant
        variants = payload.get("variants", [])
        price = variants[0].get("price", "0.0") if variants else "0.0"
        # Get image
        images = payload.get("images", [])
        image_url = images[0].get("src", "") if images else ""
        
        try:
            stmt = text("""
                INSERT INTO products (product_id, title, price, image_url, updated_at)
                VALUES (:product_id, :title, :price, :image_url, CURRENT_TIMESTAMP)
                ON CONFLICT (product_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    price = EXCLUDED.price,
                    image_url = EXCLUDED.image_url,
                    updated_at = CURRENT_TIMESTAMP
            """)
            await db.execute(stmt, {
                "product_id": product_id,
                "title": title,
                "price": price,
                "image_url": image_url
            })
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to process products/update: {e}")
            raise HTTPException(status_code=500, detail="Internal processing error")
    else:
        logger.info(f"Received unhandled topic: {topic}")

    return {"status": "ok", "message": "Webhook processed"}
