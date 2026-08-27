import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from database.connection import get_db_session
from services.ai_director import generate_script
from services.schemas import DirectorSpec

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Director"])

class ScriptGenerationRequest(BaseModel):
    product_id: str
    creator_id: str

@router.post("/generate-script", response_model=DirectorSpec)
async def api_generate_script(
    payload: ScriptGenerationRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Synchronous endpoint for n8n to request a new AI-generated TikTok script.
    """
    # 1. Fetch product details
    stmt = text("SELECT title, price FROM products WHERE product_id = :product_id")
    result = await db.execute(stmt, {"product_id": payload.product_id})
    product = result.fetchone()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in catalog")
        
    product_title = product.title
    product_price = str(product.price)
    trace_id = f"trace_{uuid.uuid4().hex[:12]}"
    
    # 2. Invoke AI Director (Synchronous as per user request)
    logger.info(f"Triggering AI Director for product {payload.product_id} (Trace: {trace_id})")
    try:
        script = await generate_script(
            product_title=product_title,
            product_price=product_price,
            product_id=payload.product_id,
            creator_id=payload.creator_id,
            trace_id=trace_id
        )
        return script
    except Exception as e:
        logger.error(f"AI Director generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI script")
