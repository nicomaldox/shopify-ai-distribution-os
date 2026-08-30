from fastapi import APIRouter
from sqlalchemy import text
from database.connection import get_db_session

router = APIRouter(prefix="/frontend", tags=["Frontend Data"])

@router.get("/earnings")
async def get_earnings():
    async for db in get_db_session():
        stmt = text("SELECT ledger_id, transaction_type, amount, status, TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as date FROM commission_ledger ORDER BY created_at DESC LIMIT 10")
        result = await db.execute(stmt)
        return {"data": [dict(row) for row in result.mappings().all()]}
        
@router.get("/audit-ledger")
async def get_audit_ledger():
    async for db in get_db_session():
        stmt = text("SELECT ledger_id, creator_id, order_id, transaction_type, amount, status, TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as date FROM commission_ledger ORDER BY created_at DESC LIMIT 50")
        result = await db.execute(stmt)
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
