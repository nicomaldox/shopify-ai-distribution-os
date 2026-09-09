import pytest
import os
import sys
from unittest.mock import patch, AsyncMock
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/apps/core-api")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/packages/video-factory")))

from main import app
from services.video_jobs_service import create_job, update_job, publish_job, reject_job, get_job, list_published_jobs

@pytest.mark.asyncio
async def test_hitl_catalog_endpoints():
    """Verify GET /frontend/products and GET /frontend/creators."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Products endpoint
        prod_resp = await client.get("/frontend/products")
        assert prod_resp.status_code == 200
        prods = prod_resp.json().get("products", [])
        assert isinstance(prods, list)

        # 2. Creators endpoint
        creator_resp = await client.get("/frontend/creators")
        assert creator_resp.status_code == 200
        creators = creator_resp.json().get("creators", [])
        assert isinstance(creators, list)

@pytest.mark.asyncio
async def test_hitl_video_publishing_and_gating():
    """
    Verify the 2-stage HITL approval gate:
    1. Render job is created with product_id & creator_id
    2. Before publication, GET /frontend/tasks does NOT include the job
    3. Admin approves & publishes via POST /video-jobs/{id}/publish
    4. GET /frontend/tasks now delivers the published job to Creator Studio
    5. Rejection marks the job REJECTED and withholds it from creators
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Submit video render job
        payload = {
            "director_spec": {
                "visual_hook": "Screen recording showing automated sales notifications.",
                "narration_text": "Tired of manual influencer outreach? Try Shopify AI Distribution OS! #Ad",
                "pacing_notes": ["0-3s: Rapid high-energy visual hook", "4-15s: Demo"],
                "ad_disclosures": ["#Ad"]
            },
            "product_id": "prod_999999999",
            "creator_id": "550e8400-e29b-41d4-a716-446655440000"
        }

        with patch("routers.video_jobs.run_rendering_pipeline", new=AsyncMock()):
            resp = await client.post("/video-jobs/render", json=payload)
            assert resp.status_code == 202
            data = resp.json()
            job_id = data["job_id"]

            # Simulate render completing, but NOT yet published (Pending Review)
            await update_job(
                job_id=job_id,
                status="COMPLETED",
                video_url=f"/static/videos/final_{job_id}.mp4",
                local_path=f"/media/videos/final_{job_id}.mp4"
            )

            # Step 2: Gating Verification - Creator Studio must NOT see unapproved job
            tasks_before = await client.get("/frontend/tasks")
            assert tasks_before.status_code == 200
            task_ids_before = [t["job_id"] for t in tasks_before.json().get("tasks", [])]
            assert job_id not in task_ids_before, "Unpublished video must NOT appear in Creator Studio!"

            # Step 3: HITL Checkpoint 2 - Admin approves and publishes
            pub_resp = await client.post(f"/video-jobs/{job_id}/publish")
            assert pub_resp.status_code == 200
            assert pub_resp.json()["status"] == "PUBLISHED"

            # Step 4: Verification - Creator Studio now sees published job
            tasks_after = await client.get("/frontend/tasks")
            assert tasks_after.status_code == 200
            task_ids_after = [t["job_id"] for t in tasks_after.json().get("tasks", [])]
            assert job_id in task_ids_after, "Published video must appear in Creator Studio!"

            # Step 5: Test Reject endpoint on a different job
            reject_payload = {
                "director_spec": {
                    "visual_hook": "Bad quality video hook",
                    "narration_text": "Bad narration text",
                    "pacing_notes": [],
                    "ad_disclosures": ["#Ad"]
                }
            }
            rej_resp = await client.post("/video-jobs/render", json=reject_payload)
            rej_job_id = rej_resp.json()["job_id"]

            rej_action = await client.post(f"/video-jobs/{rej_job_id}/reject")
            assert rej_action.status_code == 200
            assert rej_action.json()["status"] == "REJECTED"

            # Check rejection does not appear in creator tasks
            tasks_rej = await client.get("/frontend/tasks")
            task_ids_rej = [t["job_id"] for t in tasks_rej.json().get("tasks", [])]
            assert rej_job_id not in task_ids_rej
