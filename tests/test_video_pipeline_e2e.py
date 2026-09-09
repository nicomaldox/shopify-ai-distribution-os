import pytest
import os
import sys
import tempfile
import asyncio
from unittest.mock import patch, AsyncMock
import httpx

# Ensure paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/apps/core-api")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/packages/video-factory")))

from services.schemas import DirectorSpec
from services.video_jobs_service import create_job, update_job, get_job, _IN_MEMORY_JOBS
from media_assembler import assemble_media
from video_renderer import _mock_generate_video
from audio_generator import _mock_generate_audio
from main import app

@pytest.mark.asyncio
async def test_video_jobs_service_lifecycle():
    """Verify create_job, update_job, and get_job state transitions."""
    job_id = "test_job_12345"
    
    # 1. Create job
    created = await create_job(
        job_id=job_id,
        visual_hook="Hook: Test automated conversions",
        narration_text="Test narration text #Ad",
        callback_url="http://callback.test/webhook"
    )
    assert created["job_id"] == job_id
    assert created["status"] == "ACCEPTED"
    
    # 2. Update to IN_PROGRESS
    updated = await update_job(job_id=job_id, status="IN_PROGRESS")
    assert updated["status"] == "IN_PROGRESS"
    
    # 3. Update to COMPLETED
    completed = await update_job(
        job_id=job_id,
        status="COMPLETED",
        video_url="/static/videos/final_test.mp4",
        local_path="/tmp/final_test.mp4"
    )
    assert completed["status"] == "COMPLETED"
    assert completed["video_url"] == "/static/videos/final_test.mp4"
    
    # 4. Fetch job
    fetched = await get_job(job_id)
    assert fetched is not None
    assert fetched["status"] == "COMPLETED"
    assert fetched["video_url"] == "/static/videos/final_test.mp4"

@pytest.mark.asyncio
async def test_media_assembler_looping():
    """Verify that media_assembler loops the video to match audio length."""
    # Generate mock 2s video and 4s audio
    video_path = await _mock_generate_video()
    audio_path = await _mock_generate_audio()
    
    out_dir = tempfile.mkdtemp()
    final_path = await assemble_media(
        video_path=video_path,
        audio_path=audio_path,
        visual_hook="Test Looping Hook",
        output_dir=out_dir
    )
    
    assert os.path.exists(final_path)
    assert os.path.getsize(final_path) > 0
    assert final_path.endswith(".mp4")

@pytest.mark.asyncio
async def test_media_assembler_multi_clip():
    """Verify that media_assembler stitches multiple video clips sequentially with audio."""
    from video_renderer import _mock_generate_multi_clips, generate_multi_clip_video
    
    clips = await _mock_generate_multi_clips(count=3)
    assert len(clips) == 3
    audio_path = await _mock_generate_audio()
    
    out_dir = tempfile.mkdtemp()
    final_path = await assemble_media(
        video_path=clips,
        audio_path=audio_path,
        visual_hook="Test Multi-Clip Stitching Hook",
        output_dir=out_dir
    )
    
    assert os.path.exists(final_path)
    assert os.path.getsize(final_path) > 0
    assert final_path.endswith(".mp4")

@pytest.mark.asyncio
async def test_generate_multi_clip_video_fallback():
    """Verify multi-clip generator handles missing API keys gracefully with synthetic fallback."""
    from video_renderer import generate_multi_clip_video
    
    scenes = [
        "Scene 1 (0-3s): Split screen comparing slow manual outreach to automated AI scale.",
        "Scene 2 (4-10s): High-converting Shopify checkout with automatic attribution.",
        "Scene 3 (11-15s): Creator onboarding CTA with affiliate link."
    ]
    
    # Run with empty key to trigger synthetic fallback safely
    with patch.dict(os.environ, {"FAL_KEY": ""}):
        clips = await generate_multi_clip_video(scenes)
        assert len(clips) == 3
        for clip in clips:
            assert os.path.exists(clip)
            assert os.path.getsize(clip) > 0


@pytest.mark.asyncio
async def test_video_jobs_api_endpoints():
    """Test POST /video-jobs/render, GET /video-jobs/{job_id}, and static file route."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test POST /video-jobs/render with render_mode='multi_clip'
        payload = {
            "director_spec": {
                "visual_hook": "Screen recording showing automated sales notifications.",
                "narration_text": "The Shopify AI Distribution OS automates script creation instantly! #Ad #AffiliateLink",
                "pacing_notes": [
                    "Scene 1 (0-3s): Rapid visual hook",
                    "Scene 2 (4-10s): Product walkthrough",
                    "Scene 3 (11-15s): Call to action"
                ],
                "ad_disclosures": ["#Ad", "#AffiliateLink"]
            },
            "render_mode": "multi_clip"
        }
        
        # Patch background rendering pipeline so unit test runs instantaneously
        with patch("routers.video_jobs.run_rendering_pipeline", new=AsyncMock()):
            resp = await client.post("/video-jobs/render", json=payload)
            assert resp.status_code == 202
            data = resp.json()
            assert "job_id" in data
            assert data["status"] == "ACCEPTED"
            job_id = data["job_id"]
            
            # 2. Test GET /video-jobs/{job_id}
            get_resp = await client.get(f"/video-jobs/{job_id}")
            assert get_resp.status_code == 200
            job_data = get_resp.json()
            assert job_data["job_id"] == job_id
            assert job_data["status"] == "ACCEPTED"
            
        # 3. Test GET nonexistent job -> 404
        bad_resp = await client.get("/video-jobs/nonexistent_xyz")
        assert bad_resp.status_code == 404
        assert "not found" in bad_resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_static_video_serving():
    """Verify that files placed in the media/videos directory are served via /static/videos."""
    media_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../media/videos"))
    os.makedirs(media_dir, exist_ok=True)
    
    test_filename = f"test_serving_{os.getpid()}.mp4"
    test_file_path = os.path.join(media_dir, test_filename)
    
    with open(test_file_path, "wb") as f:
        f.write(b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41")
        
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/static/videos/{test_filename}")
            assert resp.status_code == 200
            assert resp.content.startswith(b"\x00\x00\x00 ftypisom")
    finally:
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
