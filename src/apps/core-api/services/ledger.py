import logging
import os
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Default commission, dynamically loadable from env to be easily changeable.
# In the future, this can be overridden by a column on the creators table.
DEFAULT_COMMISSION_PERCENTAGE = Decimal(os.getenv("DEFAULT_COMMISSION_PERCENTAGE", "20.00"))

async def record_commission_earn(db: AsyncSession, order_id: str, total_price: str, creator_id: str) -> None:
    """
    Calculates and records an EARN transaction on the append-only ledger.
    Uses strict Decimal math to prevent floating point rounding errors.
    """
    try:
        # 1. Calculate precise commission amount
        price_dec = Decimal(str(total_price))
        rate_dec = DEFAULT_COMMISSION_PERCENTAGE / Decimal("100")
        
        # Round to 4 decimal places as per NUMERIC(18,4) schema
        commission_amount = (price_dec * rate_dec).quantize(Decimal("0.0000"), rounding=ROUND_HALF_UP)
        
        # 2. Insert into the immutable ledger
        stmt = text("""
            INSERT INTO commission_ledger (creator_id, order_id, transaction_type, amount, status)
            VALUES (:creator_id, :order_id, 'EARN', :amount, 'PENDING')
        """)
        
        await db.execute(stmt, {
            "creator_id": creator_id,
            "order_id": order_id,
            "amount": commission_amount
        })
        
        logger.info(f"Ledger EARN recorded: {commission_amount} for Order {order_id} (Creator {creator_id})")
    except Exception as e:
        logger.error(f"Failed to record commission EARN for order {order_id}: {e}")
        raise

async def record_refund_reversal(db: AsyncSession, order_id: str, refund_amount: str) -> None:
    """
    Calculates and records a REVERSAL transaction based on a proportional refund.
    """
    try:
        refund_dec = Decimal(str(refund_amount))
        
        # 1. Look up the original order's total price to determine the effective rate
        stmt_order = text("""
            SELECT total_price, attributed_creator_id 
            FROM orders 
            WHERE order_id = :order_id
        """)
        res_order = await db.execute(stmt_order, {"order_id": order_id})
        order_record = res_order.fetchone()
        
        if not order_record or not order_record.attributed_creator_id:
            logger.info(f"No creator attributed for refunded order {order_id}. Skipping reversal.")
            return
            
        original_price = Decimal(str(order_record.total_price))
        creator_id = order_record.attributed_creator_id
        
        # Avoid division by zero if original order was strangely $0
        if original_price == Decimal("0"):
            logger.warning(f"Original order {order_id} price was 0. Cannot compute proportional refund.")
            return
            
        # 2. Calculate the exact proportional ratio
        # Ratio = refund_amount / original_price
        refund_ratio = refund_dec / original_price
        
        # 3. Look up the original EARN commission amount
        stmt_earn = text("""
            SELECT SUM(amount) 
            FROM commission_ledger 
            WHERE order_id = :order_id AND transaction_type = 'EARN'
        """)
        res_earn = await db.execute(stmt_earn, {"order_id": order_id})
        original_earn = res_earn.scalar()
        
        if not original_earn:
            logger.warning(f"No original EARN found for order {order_id}. Cannot reverse.")
            return
            
        original_earn_dec = Decimal(str(original_earn))
        
        # 4. Calculate exact reversal amount
        reversal_amount = -(original_earn_dec * refund_ratio).quantize(Decimal("0.0000"), rounding=ROUND_HALF_UP)
        
        # 5. Insert negative transaction into the append-only ledger
        stmt_rev = text("""
            INSERT INTO commission_ledger (creator_id, order_id, transaction_type, amount, status)
            VALUES (:creator_id, :order_id, 'REVERSAL', :amount, 'CLEARED')
        """)
        
        await db.execute(stmt_rev, {
            "creator_id": creator_id,
            "order_id": order_id,
            "amount": reversal_amount
        })
        
        logger.info(f"Ledger REVERSAL recorded: {reversal_amount} for Order {order_id} (Creator {creator_id})")
        
    except Exception as e:
        logger.error(f"Failed to record refund REVERSAL for order {order_id}: {e}")
        raise
