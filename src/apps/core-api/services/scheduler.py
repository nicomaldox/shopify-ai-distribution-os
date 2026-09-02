import asyncio
import logging
from database.connection import AsyncSessionLocal
from services.shopify_sync import sync_shopify_orders

logger = logging.getLogger(__name__)

_scheduler_task: asyncio.Task | None = None
_stop_event = asyncio.Event()

SYNC_INTERVAL_SECONDS = 30

async def _polling_loop():
    """Background loop that synchronizes Shopify orders every 30 seconds."""
    logger.info(f"Shopify Order Sync background daemon started (polling every {SYNC_INTERVAL_SECONDS}s).")
    while not _stop_event.is_set():
        try:
            async with AsyncSessionLocal() as db:
                result = await sync_shopify_orders(db, limit=50)
                if result.get("new_orders", 0) > 0 or result.get("refunds_processed", 0) > 0:
                    logger.info(
                        f"Auto-Sync Complete: {result.get('new_orders')} new orders, "
                        f"{result.get('refunds_processed')} refunds processed."
                    )
        except Exception as e:
            logger.warning(f"Error in Shopify background sync loop: {e}")

        try:
            await asyncio.wait_for(_stop_event.wait(), timeout=SYNC_INTERVAL_SECONDS)
        except asyncio.TimeoutError:
            pass

    logger.info("Shopify Order Sync background daemon stopped.")

def start_scheduler():
    """Starts the background order sync task."""
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        _stop_event.clear()
        _scheduler_task = asyncio.create_task(_polling_loop())

def stop_scheduler():
    """Stops the background order sync task."""
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _stop_event.set()
        _scheduler_task.cancel()
