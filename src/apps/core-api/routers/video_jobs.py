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
    from video_renderer import generate_video, generate_multi_clip_video, is_cloud_render_enabled
    from media_assembler import assemble_media
except ImportError as e:
    logging.warning(f"Could not import video-factory modules: {e}")
    def is_cloud_render_enabled():
        return False

from services.schemas import DirectorSpec
from services.video_jobs_service import create_job, update_job, get_job, publish_job, reject_job

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/video-jobs", tags=["Video Factory"])

class VideoJobRequest(BaseModel):
    director_spec: DirectorSpec
    callback_url: Optional[str] = None
    product_id: Optional[str] = None
    creator_id: Optional[str] = None
    product_image_url: Optional[str] = None
    render_mode: Optional[str] = "multi_clip" # "multi_clip" or "loop"

async def run_rendering_pipeline(job_id: str, spec: DirectorSpec, callback_url: Optional[str], render_mode: str = "multi_clip", product_image_url: Optional[str] = None):
    MAX_SCENES = 6
    logger.info(f"Starting rendering pipeline for job {job_id} (Mode: {render_mode})")
    await update_job(job_id, status="IN_PROGRESS")
    try:
        # Check cloud status & compute cost
        is_cloud = is_cloud_render_enabled() and bool(os.environ.get("FAL_KEY"))
        scenes_count = len(spec.pacing_notes) if spec.pacing_notes else 1
        scenes_count = min(scenes_count, MAX_SCENES)
        
        if is_cloud:
            cost = 0.15 + max(0, scenes_count - 1) * 0.20 if render_mode == "multi_clip" else 0.15
        else:
            cost = 0.0000

        # Step 1: Generate Audio
        audio_path = await generate_audio(spec.narration_text)
        
        # Step 2: Generate Video (Multi-Clip vs Single Loop)
        if render_mode == "multi_clip" and spec.pacing_notes and len(spec.pacing_notes) > 1:
            scenes = spec.pacing_notes[:MAX_SCENES]
            logger.info(f"Rendering {len(scenes)} separate scene clips in parallel (max {MAX_SCENES})")
            video_paths = await generate_multi_clip_video(scenes, product_image_url)
            final_video_path = await assemble_media(video_paths, audio_path, spec.visual_hook)
        else:
            logger.info("Rendering single hero video with looping via Fal.ai")
            video_path = await generate_video(spec.visual_hook, spec.pacing_notes)
            final_video_path = await assemble_media(video_path, audio_path, spec.visual_hook)
        
        filename = os.path.basename(final_video_path)
        video_url = f"/static/videos/{filename}"
        
        await update_job(
            job_id,
            status="COMPLETED",
            video_url=video_url,
            local_path=final_video_path,
            estimated_cost_usd=cost,
            is_cloud_render=is_cloud
        )
        
        logger.info(f"Job {job_id} completed successfully. Cost: ${cost:.4f}, Cloud: {is_cloud}. Video at: {final_video_path}")
        
        # Step 4: Webhook callback to Orchestrator (e.g. n8n)
        if callback_url:
            async with httpx.AsyncClient() as client:
                await client.post(callback_url, json={
                    "job_id": job_id,
                    "status": "COMPLETED",
                    "video_url": video_url,
                    "final_video_path": final_video_path
                })
                logger.info(f"Callback sent for job {job_id}")
                
    except Exception as e:
        error_msg = str(e).strip() or f"{type(e).__name__}: {repr(e)}"
        logger.error(f"Job {job_id} failed: {error_msg}")
        await update_job(job_id, status="FAILED", error_message=error_msg)
        if callback_url:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(callback_url, json={
                        "job_id": job_id,
                        "status": "FAILED",
                        "error": error_msg
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
    
    # Record job in database / in-memory store
    pacing_str = ", ".join(payload.director_spec.pacing_notes) if payload.director_spec.pacing_notes else None
    tags_str = ", ".join(payload.director_spec.ad_disclosures) if payload.director_spec.ad_disclosures else None
    
    scenes_count = len(payload.director_spec.pacing_notes) if payload.director_spec.pacing_notes else 1
    scenes_count = min(scenes_count, 6)
    mode = payload.render_mode or "multi_clip"
    
    is_cloud = is_cloud_render_enabled() and bool(os.environ.get("FAL_KEY"))
    if is_cloud:
        est_cost = 0.15 + max(0, scenes_count - 1) * 0.20 if mode == "multi_clip" else 0.15
    else:
        est_cost = 0.0000

    await create_job(
        job_id=job_id,
        visual_hook=payload.director_spec.visual_hook,
        narration_text=payload.director_spec.narration_text,
        callback_url=payload.callback_url,
        product_id=payload.product_id,
        creator_id=payload.creator_id,
        pacing_notes=pacing_str,
        ad_disclosures=tags_str,
        render_mode=mode,
        scenes_count=scenes_count,
        estimated_cost_usd=est_cost,
        is_cloud_render=is_cloud
    )
    
    background_tasks.add_task(
        run_rendering_pipeline,
        job_id,
        payload.director_spec,
        payload.callback_url,
        mode,
        payload.product_image_url
    )
    
    return {"job_id": job_id, "status": "ACCEPTED", "message": "Rendering job started"}

@router.get("/{job_id}")
async def get_video_job_status(job_id: str):
    """
    Poll the status of an asynchronous video rendering job by job_id.
    """
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job

@router.post("/{job_id}/publish")
async def api_publish_video_job(job_id: str):
    """
    HITL Checkpoint 2: Approves the rendered video and publishes it to Creator Studio.
    """
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    await publish_job(job_id)
    return {"job_id": job_id, "status": "PUBLISHED", "message": "Video successfully published to Creator Studio"}

@router.post("/{job_id}/reject")
async def api_reject_video_job(job_id: str):
    """
    HITL Checkpoint 2: Rejects the rendered video during review.
    """
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    await reject_job(job_id)
    return {"job_id": job_id, "status": "REJECTED", "message": "Video rejected"}

