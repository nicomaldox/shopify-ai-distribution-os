import os
from fastapi import APIRouter
from sqlalchemy import text
from database.connection import get_db_session

router = APIRouter(prefix="/frontend", tags=["Frontend Data"])

APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Taipei")

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
    async for db in get_db_session():
        stmt = text("SELECT trace_id, total_tokens, estimated_cost_usd, latency_ms, status FROM ai_generation_logs ORDER BY created_at DESC LIMIT 20")
        result = await db.execute(stmt)
        logs = [dict(row) for row in result.mappings().all()]
        
        agg_stmt = text("SELECT COALESCE(SUM(total_tokens), 0) as total, COALESCE(SUM(estimated_cost_usd), 0) as cost, COALESCE(AVG(claims_accuracy_score), 1.0) as acc FROM ai_generation_logs")
        agg_res = await db.execute(agg_stmt)
        agg_row = agg_res.mappings().first()
        
        return {
            "metrics": {
                "total_tokens": int(agg_row["total"]),
                "cost_usd": float(agg_row["cost"]),
                "accuracy": float(agg_row["acc"])
            },
            "logs": logs
        }
