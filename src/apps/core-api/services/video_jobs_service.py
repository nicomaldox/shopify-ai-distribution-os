import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import text
from database.connection import AsyncSessionLocal, engine

import asyncio

logger = logging.getLogger(__name__)

# Resilient in-memory fallback for testing or offline environments
_IN_MEMORY_JOBS: Dict[str, Dict[str, Any]] = {}
_DB_AVAILABLE: Optional[bool] = None

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS video_render_jobs (
    job_id VARCHAR(64) PRIMARY KEY,
    status VARCHAR(50) NOT NULL DEFAULT 'ACCEPTED',
    visual_hook TEXT,
    narration_text TEXT,
    video_url TEXT,
    local_path TEXT,
    error_message TEXT,
    callback_url TEXT,
    product_id VARCHAR(255),
    creator_id VARCHAR(64),
    pacing_notes TEXT,
    ad_disclosures TEXT,
    render_mode VARCHAR(32) DEFAULT 'multi_clip',
    scenes_count INT DEFAULT 1,
    estimated_cost_usd NUMERIC(10, 4) DEFAULT 0.0000,
    is_cloud_render BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

MIGRATION_SQL = """
ALTER TABLE video_render_jobs ADD COLUMN IF NOT EXISTS product_id VARCHAR(255);
ALTER TABLE video_render_jobs ADD COLUMN IF NOT EXISTS creator_id VARCHAR(64);
ALTER TABLE video_render_jobs ADD COLUMN IF NOT EXISTS pacing_notes TEXT;
ALTER TABLE video_render_jobs ADD COLUMN IF NOT EXISTS ad_disclosures TEXT;
ALTER TABLE video_render_jobs ADD COLUMN IF NOT EXISTS render_mode VARCHAR(32) DEFAULT 'multi_clip';
ALTER TABLE video_render_jobs ADD COLUMN IF NOT EXISTS scenes_count INT DEFAULT 1;
ALTER TABLE video_render_jobs ADD COLUMN IF NOT EXISTS estimated_cost_usd NUMERIC(10, 4) DEFAULT 0.0000;
ALTER TABLE video_render_jobs ADD COLUMN IF NOT EXISTS is_cloud_render BOOLEAN DEFAULT FALSE;
"""

async def ensure_table_exists() -> bool:
    """Ensures the video_render_jobs table and its columns exist in PostgreSQL if connected."""
    global _DB_AVAILABLE
    try:
        async with asyncio.timeout(2.0):
            async with engine.begin() as conn:
                await conn.execute(text(CREATE_TABLE_SQL))
                await conn.execute(text(MIGRATION_SQL))
        _DB_AVAILABLE = True
        return True
    except Exception as e:
        logger.debug(f"Database connection unavailable for video_render_jobs table creation: {e}")
        _DB_AVAILABLE = False
        return False

async def create_job(
    job_id: str,
    visual_hook: str,
    narration_text: str,
    callback_url: Optional[str] = None,
    product_id: Optional[str] = None,
    creator_id: Optional[str] = None,
    pacing_notes: Optional[str] = None,
    ad_disclosures: Optional[str] = None,
    render_mode: Optional[str] = "multi_clip",
    scenes_count: Optional[int] = 1,
    estimated_cost_usd: Optional[float] = 0.0,
    is_cloud_render: Optional[bool] = False
) -> Dict[str, Any]:
    """Records a newly accepted rendering job with optional product, creator links, and cost telemetry."""
    now = datetime.now(timezone.utc)
    job_data = {
        "job_id": job_id,
        "status": "ACCEPTED",
        "visual_hook": visual_hook,
        "narration_text": narration_text,
        "video_url": None,
        "local_path": None,
        "error_message": None,
        "callback_url": callback_url,
        "product_id": product_id,
        "creator_id": creator_id,
        "pacing_notes": pacing_notes,
        "ad_disclosures": ad_disclosures,
        "render_mode": render_mode or "multi_clip",
        "scenes_count": scenes_count or 1,
        "estimated_cost_usd": float(estimated_cost_usd or 0.0),
        "is_cloud_render": bool(is_cloud_render),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    # Always keep in-memory cache up to date
    _IN_MEMORY_JOBS[job_id] = job_data
    
    global _DB_AVAILABLE
    if _DB_AVAILABLE is False:
        return job_data
        
    try:
        async with asyncio.timeout(2.0):
            async with AsyncSessionLocal() as session:
                stmt = text("""
                    INSERT INTO video_render_jobs (
                        job_id, status, visual_hook, narration_text, callback_url, 
                        product_id, creator_id, pacing_notes, ad_disclosures,
                        render_mode, scenes_count, estimated_cost_usd, is_cloud_render,
                        created_at, updated_at
                    ) VALUES (
                        :job_id, :status, :visual_hook, :narration_text, :callback_url,
                        :product_id, :creator_id, :pacing_notes, :ad_disclosures,
                        :render_mode, :scenes_count, :estimated_cost_usd, :is_cloud_render,
                        :created_at, :updated_at
                    )
                """)
                await session.execute(stmt, {
                    "job_id": job_id,
                    "status": "ACCEPTED",
                    "visual_hook": visual_hook,
                    "narration_text": narration_text,
                    "callback_url": callback_url,
                    "product_id": product_id,
                    "creator_id": creator_id,
                    "pacing_notes": pacing_notes,
                    "ad_disclosures": ad_disclosures,
                    "render_mode": render_mode or "multi_clip",
                    "scenes_count": scenes_count or 1,
                    "estimated_cost_usd": float(estimated_cost_usd or 0.0),
                    "is_cloud_render": bool(is_cloud_render),
                    "created_at": now,
                    "updated_at": now
                })
                await session.commit()
                _DB_AVAILABLE = True
                logger.info(f"Recorded job {job_id} in database (Cost: ${estimated_cost_usd:.4f}, Cloud: {is_cloud_render}).")
    except Exception as e:
        _DB_AVAILABLE = False
        logger.debug(f"Failed to persist job {job_id} to DB (using in-memory store): {e}")
        
    return job_data

async def update_job(
    job_id: str,
    status: str,
    video_url: Optional[str] = None,
    local_path: Optional[str] = None,
    error_message: Optional[str] = None,
    estimated_cost_usd: Optional[float] = None,
    is_cloud_render: Optional[bool] = None
) -> Optional[Dict[str, Any]]:
    """Updates job status, video URL, cost, or error details in both DB and memory."""
    now = datetime.now(timezone.utc)
    
    if job_id in _IN_MEMORY_JOBS:
        _IN_MEMORY_JOBS[job_id]["status"] = status
        _IN_MEMORY_JOBS[job_id]["updated_at"] = now.isoformat()
        if video_url is not None:
            _IN_MEMORY_JOBS[job_id]["video_url"] = video_url
        if local_path is not None:
            _IN_MEMORY_JOBS[job_id]["local_path"] = local_path
        if error_message is not None:
            _IN_MEMORY_JOBS[job_id]["error_message"] = error_message
        if estimated_cost_usd is not None:
            _IN_MEMORY_JOBS[job_id]["estimated_cost_usd"] = float(estimated_cost_usd)
        if is_cloud_render is not None:
            _IN_MEMORY_JOBS[job_id]["is_cloud_render"] = bool(is_cloud_render)
            
    global _DB_AVAILABLE
    if _DB_AVAILABLE is False:
        return _IN_MEMORY_JOBS.get(job_id)
        
    try:
        async with asyncio.timeout(2.0):
            async with AsyncSessionLocal() as session:
                stmt = text("""
                    UPDATE video_render_jobs
                    SET status = :status,
                        video_url = COALESCE(:video_url, video_url),
                        local_path = COALESCE(:local_path, local_path),
                        error_message = COALESCE(:error_message, error_message),
                        estimated_cost_usd = COALESCE(:estimated_cost_usd, estimated_cost_usd),
                        is_cloud_render = COALESCE(:is_cloud_render, is_cloud_render),
                        updated_at = :updated_at
                    WHERE job_id = :job_id
                """)
                await session.execute(stmt, {
                    "job_id": job_id,
                    "status": status,
                    "video_url": video_url,
                    "local_path": local_path,
                    "error_message": error_message,
                    "estimated_cost_usd": estimated_cost_usd,
                    "is_cloud_render": is_cloud_render,
                    "updated_at": now
                })
                await session.commit()
                _DB_AVAILABLE = True
    except Exception as e:
        _DB_AVAILABLE = False
        logger.debug(f"Failed to update job {job_id} in DB (updated in-memory): {e}")
        
    return _IN_MEMORY_JOBS.get(job_id)

async def publish_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Approves and publishes a rendered video job to Creator Studio."""
    return await update_job(job_id, status="PUBLISHED")

async def reject_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Rejects a rendered video job during quality review."""
    return await update_job(job_id, status="REJECTED")

async def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves job details from the database or in-memory fallback."""
    global _DB_AVAILABLE
    if _DB_AVAILABLE is False:
        return _IN_MEMORY_JOBS.get(job_id)
        
    try:
        async with asyncio.timeout(2.0):
            async with AsyncSessionLocal() as session:
                stmt = text("""
                    SELECT job_id, status, visual_hook, narration_text, video_url, 
                           local_path, error_message, callback_url, product_id, creator_id,
                           pacing_notes, ad_disclosures, render_mode, scenes_count,
                           estimated_cost_usd, is_cloud_render, created_at, updated_at
                    FROM video_render_jobs
                    WHERE job_id = :job_id
                """)
                result = await session.execute(stmt, {"job_id": job_id})
                row = result.fetchone()
                if row:
                    _DB_AVAILABLE = True
                    return {
                        "job_id": row.job_id,
                        "status": row.status,
                        "visual_hook": row.visual_hook,
                        "narration_text": row.narration_text,
                        "video_url": row.video_url,
                        "local_path": row.local_path,
                        "error_message": row.error_message,
                        "callback_url": row.callback_url,
                        "product_id": getattr(row, "product_id", None),
                        "creator_id": getattr(row, "creator_id", None),
                        "pacing_notes": getattr(row, "pacing_notes", None),
                        "ad_disclosures": getattr(row, "ad_disclosures", None),
                        "render_mode": getattr(row, "render_mode", "multi_clip"),
                        "scenes_count": getattr(row, "scenes_count", 1),
                        "estimated_cost_usd": float(getattr(row, "estimated_cost_usd", 0.0) or 0.0),
                        "is_cloud_render": bool(getattr(row, "is_cloud_render", False)),
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    }
    except Exception as e:
        _DB_AVAILABLE = False
        logger.debug(f"Could not read job {job_id} from DB, checking in-memory: {e}")
        
    return _IN_MEMORY_JOBS.get(job_id)

async def list_published_jobs(creator_id: Optional[str] = None):
    """Retrieves all jobs with status = 'PUBLISHED' for delivery to Creator Studio."""
    global _DB_AVAILABLE
    if _DB_AVAILABLE is False:
        results = [
            job for job in _IN_MEMORY_JOBS.values()
            if job.get("status") == "PUBLISHED" and (creator_id is None or job.get("creator_id") == creator_id)
        ]
        return results

    try:
        async with asyncio.timeout(2.0):
            async with AsyncSessionLocal() as session:
                sql = """
                    SELECT 
                        j.job_id, j.status, j.visual_hook, j.narration_text, j.video_url,
                        j.product_id, j.creator_id, j.pacing_notes, j.ad_disclosures, j.created_at,
                        p.title as product_title, p.price as product_price, p.image_url as product_image,
                        al.slug, al.coupon_code
                    FROM video_render_jobs j
                    LEFT JOIN products p ON j.product_id = p.product_id
                    LEFT JOIN creators c ON j.creator_id = CAST(c.creator_id AS VARCHAR)
                    LEFT JOIN affiliate_links al ON c.creator_id = al.creator_id
                    WHERE j.status = 'PUBLISHED'
                """
                params = {}
                if creator_id:
                    sql += " AND (j.creator_id = :cid OR j.creator_id IS NULL)"
                    params["cid"] = creator_id
                sql += " ORDER BY j.created_at DESC LIMIT 20"
                
                result = await session.execute(text(sql), params)
                rows = [dict(row) for row in result.mappings().all()]
                _DB_AVAILABLE = True
                return rows
    except Exception as e:
        logger.debug(f"Could not list published jobs from DB: {e}")
        _DB_AVAILABLE = False
        return [
            job for job in _IN_MEMORY_JOBS.values()
            if job.get("status") == "PUBLISHED" and (creator_id is None or job.get("creator_id") == creator_id)
        ]

