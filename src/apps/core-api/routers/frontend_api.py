import os
import logging
from fastapi import APIRouter
from sqlalchemy import text
from database.connection import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/frontend", tags=["Frontend Data"])

APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Taipei")

DEFAULT_PRODUCTS = [
    {
        "product_id": "prod_serum_001",
        "title": "Luminous Hydrating Glow Serum (極光保濕超導精華液)",
        "price": 1280.0,
        "image_url": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=800&q=80"
    },
    {
        "product_id": "prod_cream_002",
        "title": "Revitalizing Barrier Repair Cream (賦活屏障修護乳霜)",
        "price": 1580.0,
        "image_url": "https://images.unsplash.com/photo-1608248597359-bb47265ea5b3?w=800&q=80"
    },
    {
        "product_id": "prod_oil_003",
        "title": "Gentle Botanical Cleansing Oil (植萃舒緩深層潔顏油)",
        "price": 980.0,
        "image_url": "https://images.unsplash.com/photo-1601049541289-9b1b7bbbfe19?w=800&q=80"
    }
]

DEFAULT_CREATORS = [
    {
        "creator_id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Elena Lin (美妝護膚 艾琳娜)",
        "niche": "Skincare & Clean Beauty",
        "commission_rate": 0.20,
        "slug": "elena-glow",
        "coupon_code": "ELENA10"
    },
    {
        "creator_id": "550e8400-e29b-41d4-a716-446655440002",
        "name": "Chloe Chen (護膚日記 克洛伊)",
        "niche": "Sensitive Skin Care",
        "commission_rate": 0.20,
        "slug": "chloe-skin",
        "coupon_code": "CHLOE20"
    }
]

@router.get("/earnings")
async def get_earnings():
    async for db in get_db_session():
        stmt = text("""
            SELECT 
                cl.ledger_id, 
                cl.order_id,
                COALESCE(o.total_price, 0) as order_total,
                cl.transaction_type, 
                cl.amount, 
                cl.status, 
                TO_CHAR(cl.created_at AT TIME ZONE :tz, 'YYYY-MM-DD HH24:MI:SS') as date,
                TO_CHAR(cl.created_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as iso_date
            FROM commission_ledger cl
            LEFT JOIN orders o ON cl.order_id = o.order_id
            ORDER BY cl.created_at DESC 
            LIMIT 20
        """)
        result = await db.execute(stmt, {"tz": APP_TIMEZONE})
        return {"data": [dict(row) for row in result.mappings().all()]}
        
@router.get("/audit-ledger")
async def get_audit_ledger():
    async for db in get_db_session():
        stmt = text("""
            SELECT 
                cl.ledger_id, 
                cl.creator_id, 
                cl.order_id, 
                COALESCE(o.total_price, 0) as order_total,
                cl.transaction_type, 
                cl.amount, 
                cl.status, 
                TO_CHAR(cl.created_at AT TIME ZONE :tz, 'YYYY-MM-DD HH24:MI:SS') as date,
                TO_CHAR(cl.created_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as iso_date
            FROM commission_ledger cl 
            LEFT JOIN orders o ON cl.order_id = o.order_id
            ORDER BY cl.created_at DESC 
            LIMIT 50
        """)
        result = await db.execute(stmt, {"tz": APP_TIMEZONE})
        return {"data": [dict(row) for row in result.mappings().all()]}

@router.get("/ai-metrics")
async def get_ai_metrics():
    HISTORICAL_FAL_WASTED_USD = 6.40  # Tracked credit loss from initial unoptimized debug runs
    try:
        async for db in get_db_session():
            stmt = text("SELECT trace_id, total_tokens, estimated_cost_usd, latency_ms, status FROM ai_generation_logs ORDER BY created_at DESC LIMIT 20")
            result = await db.execute(stmt)
            logs = [dict(row) for row in result.mappings().all()]
            
            agg_stmt = text("SELECT COALESCE(SUM(total_tokens), 0) as total, COALESCE(SUM(estimated_cost_usd), 0) as cost, COALESCE(AVG(claims_accuracy_score), 1.0) as acc FROM ai_generation_logs")
            agg_res = await db.execute(agg_stmt)
            agg_row = agg_res.mappings().first()
            
            # Video jobs aggregation & cost tracking
            v_agg_stmt = text("""
                SELECT 
                    COALESCE(SUM(estimated_cost_usd), 0) as video_cost,
                    COUNT(*) as total_renders,
                    COALESCE(SUM(CASE WHEN is_cloud_render THEN 1 ELSE 0 END), 0) as cloud_renders
                FROM video_render_jobs
            """)
            v_agg_res = await db.execute(v_agg_stmt)
            v_agg_row = v_agg_res.mappings().first()
            
            # Recent video render jobs
            v_stmt = text("""
                SELECT 
                    job_id, status, 
                    COALESCE(render_mode, 'multi_clip') as render_mode, 
                    COALESCE(scenes_count, 1) as scenes_count, 
                    COALESCE(estimated_cost_usd, 0) as estimated_cost_usd, 
                    COALESCE(is_cloud_render, false) as is_cloud_render, 
                    visual_hook, 
                    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_time
                FROM video_render_jobs
                ORDER BY created_at DESC
                LIMIT 20
            """)
            v_res = await db.execute(v_stmt)
            video_jobs = [dict(row) for row in v_res.mappings().all()]
            
            llm_cost = float(agg_row["cost"])
            live_video_cost = float(v_agg_row["video_cost"])
            total_fal_expenses = HISTORICAL_FAL_WASTED_USD + live_video_cost
            total_compute_cost = llm_cost + total_fal_expenses

            return {
                "metrics": {
                    "total_tokens": int(agg_row["total"]),
                    "cost_usd": total_compute_cost,
                    "llm_cost_usd": llm_cost,
                    "historical_fal_wasted_usd": HISTORICAL_FAL_WASTED_USD,
                    "live_fal_cost_usd": live_video_cost,
                    "total_fal_cost_usd": total_fal_expenses,
                    "total_compute_cost_usd": total_compute_cost,
                    "accuracy": float(agg_row["acc"]),
                    "total_renders": int(v_agg_row["total_renders"]),
                    "cloud_renders": int(v_agg_row["cloud_renders"])
                },
                "logs": logs,
                "video_jobs": video_jobs
            }
    except Exception as e:
        logger.warning(f"Error fetching AI metrics from database: {e}")
        return {
            "metrics": {
                "total_tokens": 0,
                "cost_usd": HISTORICAL_FAL_WASTED_USD,
                "llm_cost_usd": 0.0,
                "historical_fal_wasted_usd": HISTORICAL_FAL_WASTED_USD,
                "live_fal_cost_usd": 0.0,
                "total_fal_cost_usd": HISTORICAL_FAL_WASTED_USD,
                "total_compute_cost_usd": HISTORICAL_FAL_WASTED_USD,
                "accuracy": 1.0,
                "total_renders": 0,
                "cloud_renders": 0
            },
            "logs": [],
            "video_jobs": []
        }

@router.get("/products")
async def get_frontend_products():
    """Returns available products in catalog for Admin Studio selection."""
    try:
        async for db in get_db_session():
            stmt = text("SELECT product_id, title, price, image_url FROM products ORDER BY title ASC")
            result = await db.execute(stmt)
            products = [dict(row) for row in result.mappings().all()]
            if products:
                return {"products": products}
    except Exception as e:
        logger.debug(f"Database query failed for products, using default fallback: {e}")
    return {"products": DEFAULT_PRODUCTS}

@router.get("/creators")
async def get_frontend_creators():
    """Returns creators roster with affiliate link and promo codes."""
    try:
        async for db in get_db_session():
            stmt = text("""
                SELECT 
                    c.creator_id, 
                    c.name, 
                    c.niche, 
                    c.commission_rate,
                    al.slug,
                    al.coupon_code
                FROM creators c
                LEFT JOIN affiliate_links al ON c.creator_id = al.creator_id
                ORDER BY c.name ASC
            """)
            result = await db.execute(stmt)
            creators = [dict(row) for row in result.mappings().all()]
            if creators:
                return {"creators": creators}
    except Exception as e:
        logger.debug(f"Database query failed for creators, using default fallback: {e}")
    return {"creators": DEFAULT_CREATORS}

@router.get("/tasks")
async def get_frontend_tasks(creator_id: str = None):
    """
    Returns tasks for Creator Studio, STRICTLY gated by status = 'PUBLISHED'.
    Unapproved drafts and rendering jobs are never exposed to creators.
    """
    from services.video_jobs_service import list_published_jobs
    tasks = await list_published_jobs(creator_id)
    return {"tasks": tasks}


