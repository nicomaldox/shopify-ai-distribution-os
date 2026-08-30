import logging
import uuid
import httpx
import sys
import os
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional

# Add video-factory to sys.path so we can import it in this PoC
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../packages/video-factory"))

try:
    from audio_generator import generate_audio
    from video_renderer import generate_video
    from media_assembler import assemble_media
except ImportError as e:
    logging.warning(f"Could not import video-factory modules: {e}")

from services.schemas import DirectorSpec

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/video-jobs", tags=["Video Factory"])

class VideoJobRequest(BaseModel):
    director_spec: DirectorSpec
    callback_url: Optional[str] = None

async def run_rendering_pipeline(job_id: str, spec: DirectorSpec, callback_url: Optional[str]):
    logger.info(f"Starting rendering pipeline for job {job_id}")
    try:
        # Step 1: Generate Audio
        audio_path = await generate_audio(spec.narration_text)
        
        # Step 2: Generate Video
        video_path = await generate_video(spec.visual_hook, spec.pacing_notes)
        
        # Step 3: Assemble Media
        final_video_path = await assemble_media(video_path, audio_path, spec.visual_hook)
        
        logger.info(f"Job {job_id} completed successfully. Final video at: {final_video_path}")
        
        # Step 4: Webhook callback to Orchestrator (e.g. n8n)
        if callback_url:
            async with httpx.AsyncClient() as client:
                await client.post(callback_url, json={
                    "job_id": job_id,
                    "status": "COMPLETED",
                    "final_video_path": final_video_path
                })
                logger.info(f"Callback sent for job {job_id}")
                
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        if callback_url:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(callback_url, json={
                        "job_id": job_id,
                        "status": "FAILED",
                        "error": str(e)
                    })
            except Exception as cb_err:
                logger.error(f"Failed to send failure callback for job {job_id}: {cb_err}")

@router.post("/render", status_code=202)
async def api_trigger_video_render(
    payload: VideoJobRequest,
    background_tasks: BackgroundTasks
):
    """
    Asynchronous endpoint to trigger the video and audio rendering factory.
    Returns 202 Accepted immediately without blocking.
    """
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    
    background_tasks.add_task(
        run_rendering_pipeline,
        job_id,
        payload.director_spec,
        payload.callback_url
    )
    
    return {"job_id": job_id, "status": "ACCEPTED", "message": "Rendering job started"}
