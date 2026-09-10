import os
import uuid
import logging
import tempfile
import urllib.parse
import ipaddress
import httpx
import asyncio
import shutil
import subprocess
import fal_client

logger = logging.getLogger(__name__)

def get_ffmpeg_binary() -> str:
    return shutil.which("ffmpeg") or shutil.which("ffmpeg.exe") or "ffmpeg"

def is_cloud_render_enabled() -> bool:
    """
    Checks if external cloud GPU rendering (e.g. paid Fal.ai) is explicitly enabled.
    Defaults to False to prevent unnecessary cloud API spending.
    """
    return os.environ.get("ENABLE_CLOUD_VIDEO_RENDER", "false").lower() in ("true", "1")


def is_safe_url(url: str) -> bool:
    """
    SSRF Defense: Validates the URL protocol and ensures it does not point to internal IP ranges.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ["https"]:
            return False
            
        hostname = parsed.hostname
        if not hostname:
            return False
            
        # Basic exact string matches for localhost
        if hostname.lower() in ["localhost", "127.0.0.1", "169.254.169.254"]:
            return False
            
        try:
            ip = ipaddress.ip_address(hostname)
            # Block private, loopback, and link-local
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        except ValueError:
            # It's a hostname, skip full DNS resolution for this PoC
            pass
            
        return True
    except Exception:
        return False

async def _render_single_fal_clip(prompt: str, num_frames: int = 81) -> str:
    """Helper to dispatch, poll, and download a single video clip from Fal.ai using fal_client."""
    # Ensure fal_key is set in env
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        raise ValueError("FAL_KEY is required for cloud rendering.")
    
    # Use matching Wan 2.1 T2V endpoint
    endpoint = "fal-ai/wan-t2v"
    
    try:
        logger.info(f"Submitting Fal.ai T2V job for prompt: {prompt[:30]}... (frames: {num_frames})")
        # Use subscribe_async to automatically handle queue and polling
        result = await fal_client.subscribe_async(
            endpoint,
            arguments={
                "prompt": prompt,
                "aspect_ratio": "9:16",
                "resolution": "480p"  # 480p to save costs
            }
        )
        
        # Extract video URL
        video_url = None
        if "video" in result and isinstance(result["video"], dict):
            video_url = result["video"].get("url")
        elif "url" in result:
            video_url = result.get("url")
            
        if not video_url:
            raise RuntimeError(f"Could not find video URL in result: {result}")
            
        if not is_safe_url(video_url):
            raise ValueError(f"SSRF Alert: Blocked unsafe video URL: {video_url}")
            
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"clip_{uuid.uuid4().hex}.mp4")

        logger.info(f"Downloading clip from {video_url}...")
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', video_url) as stream_resp:
                stream_resp.raise_for_status()
                with open(output_path, 'wb') as f:
                    async for chunk in stream_resp.aiter_bytes():
                        f.write(chunk)

        logger.info(f"Clip saved successfully: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Fal.ai T2V rendering failed: {e}")
        raise e

async def _render_single_fal_i2v_clip(prompt: str, image_url: str, num_frames: int = 81) -> str:
    """Helper to dispatch, poll, and download a single image-to-video clip from Fal.ai using fal_client."""
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        raise ValueError("FAL_KEY is required for cloud rendering.")
        
    if not image_url:
        raise ValueError("image_url is required for I2V generation.")
    
    endpoint = "fal-ai/wan-i2v"
    
    try:
        logger.info(f"Submitting Fal.ai I2V job for prompt: {prompt[:30]}... (frames: {num_frames})")
        result = await fal_client.subscribe_async(
            endpoint,
            arguments={
                "prompt": prompt,
                "image_url": image_url,
                "aspect_ratio": "9:16",
                "resolution": "480p",
                "num_frames": num_frames
            }
        )
        
        video_url = None
        if "video" in result and isinstance(result["video"], dict):
            video_url = result["video"].get("url")
        elif "url" in result:
            video_url = result.get("url")
            
        if not video_url:
            raise RuntimeError(f"Could not find video URL in result: {result}")
            
        if not is_safe_url(video_url):
            raise ValueError(f"SSRF Alert: Blocked unsafe video URL: {video_url}")
            
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"clip_{uuid.uuid4().hex}.mp4")

        logger.info(f"Downloading clip from {video_url}...")
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', video_url) as stream_resp:
                stream_resp.raise_for_status()
                with open(output_path, 'wb') as f:
                    async for chunk in stream_resp.aiter_bytes():
                        f.write(chunk)

        logger.info(f"Clip saved successfully: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Fal.ai I2V rendering failed: {e}")
        raise e

async def generate_video(visual_hook: str, pacing_notes: list[str]) -> str:
    """
    Generates a single 9:16 vertical video.
    By default, uses local high-fidelity synthetic video generation to prevent cloud costs.
    Cloud Fal.ai rendering is only executed if ENABLE_CLOUD_VIDEO_RENDER=true is explicitly set.
    """
    fal_key = os.environ.get("FAL_KEY")
    if not is_cloud_render_enabled() or not fal_key:
        logger.info("Cloud video rendering disabled or FAL_KEY absent. Using zero-cost local synthetic video.")
        return await _mock_generate_video(scene_title=visual_hook)
        
    prompt = f"{visual_hook}. Pacing notes: {', '.join(pacing_notes)}"
    logger.info(f"Triggering Fal.ai Video Generation. Prompt: {prompt[:50]}...")
    
    # Budget gate
    COST_PER_CLIP_ESTIMATE = 0.15 # $0.05/s * 3s
    MAX_BUDGET_PER_RENDER = 2.00
    if COST_PER_CLIP_ESTIMATE > MAX_BUDGET_PER_RENDER:
        logger.error(f"Estimated cost ${COST_PER_CLIP_ESTIMATE:.2f} exceeds budget ${MAX_BUDGET_PER_RENDER}")
        return await _mock_generate_video(scene_title=visual_hook)
        
    try:
        return await _render_single_fal_clip(prompt)
    except Exception as e:
        logger.warning(f"Fal.ai single video generation failed: {e}. Falling back to mock.")
        return await _mock_generate_video(scene_title=visual_hook)

async def generate_multi_clip_video(scenes: list[str], product_image_url: str = None) -> list[str]:
    """
    Generates multiple 9:16 vertical video clips (max 6 scenes).
    By default, uses local high-fidelity synthetic multi-clip generation to prevent cloud costs.
    Cloud Fal.ai rendering is only executed if ENABLE_CLOUD_VIDEO_RENDER=true is explicitly set.
    Uses hybrid logic: Scene 1 (index 0) is T2V, Scenes 2+ (index 1+) are I2V (if image provided).
    """
    MAX_SCENES = 6
    scenes = scenes[:MAX_SCENES]

    fal_key = os.environ.get("FAL_KEY")
    if not is_cloud_render_enabled() or not fal_key:
        logger.info("Cloud video rendering disabled or FAL_KEY absent. Using zero-cost local synthetic multi-clips.")
        return await _mock_generate_multi_clips(scenes=scenes)

    logger.info(f"Triggering Hybrid Multi-Clip Video Generation for {len(scenes)} scenes via Fal.ai.")
    
    # Budget gate
    COST_PER_CLIP_ESTIMATE = 0.20 # $0.04/s * 5s
    estimated_cost = len(scenes) * COST_PER_CLIP_ESTIMATE
    MAX_BUDGET_PER_RENDER = 4.00
    if estimated_cost > MAX_BUDGET_PER_RENDER:
        logger.error(f"Estimated cost ${estimated_cost:.2f} exceeds budget ${MAX_BUDGET_PER_RENDER}")
        return await _mock_generate_multi_clips(scenes=scenes)
        
    def _clean_prompt(raw: str) -> str:
        # Strip timing prefixes like 'Scene 1 (0-3s): ' or '(0-3s)' and any bracketed wrappers
        p = raw.strip()
        if "):" in p:
            p = p.split("):", 1)[1].strip()
        elif ") " in p:
            p = p.split(") ", 1)[1].strip()
        elif ":" in p and any(p.lower().startswith(f"scene {i}") for i in range(1, 10)):
            p = p.split(":", 1)[1].strip()
        # Clean out brackets and quotes
        p = p.replace("[", "").replace("]", "").replace('"', '').strip()
        return f"Cinematic 9:16 vertical video, photorealistic UGC beauty style, natural lighting, high fidelity 4k texture: {p}"

    clean_prompts = [_clean_prompt(s) for s in scenes]

    # Concurrency limit for Fal.ai rendering tasks (4 concurrent cuts rendering time down to ~60-90s)
    sem = asyncio.Semaphore(4)

    async def _throttled_call(fn, *args, **kwargs):
        async with sem:
            return await fn(*args, **kwargs)

    tasks = []
    for idx, prompt in enumerate(clean_prompts):
        if idx == 0 or not product_image_url:
            # Scene 1 (Hook) is T2V, 81 frames (~5s at 16fps)
            tasks.append(_throttled_call(_render_single_fal_clip, prompt, num_frames=81))
        elif idx == 1:
            # Scene 2 (Core Benefit) is I2V, 81 frames (~5s at 16fps)
            tasks.append(_throttled_call(_render_single_fal_i2v_clip, prompt, product_image_url, num_frames=81))
        else:
            # Scene 3-6 (Experience) is I2V, 81 frames (~5s at 16fps)
            tasks.append(_throttled_call(_render_single_fal_i2v_clip, prompt, product_image_url, num_frames=81))
            
    results = await asyncio.gather(*tasks, return_exceptions=True)

    clips = []
    for idx, res in enumerate(results):
        if isinstance(res, str) and os.path.exists(res):
            clips.append(res)
        else:
            logger.warning(f"Clip {idx} failed ({res}). Generating synthetic fallback.")
            scene_label = scenes[idx] if idx < len(scenes) else f"Scene {idx+1}"
            mock_clip = await _mock_generate_video(
                color_hex="0x1e1b4b" if idx == 0 else ("0x0f172a" if idx == 1 else "0x064e3b"), 
                duration=5,
                scene_title=scene_label
            )
            clips.append(mock_clip)

    return clips

async def _mock_generate_video(color_hex: str = "0x1a1a2e", duration: int = 5, scene_title: str = "Scene") -> str:
    """Generates a valid 9:16 vertical MP4 video using ffmpeg for offline and zero-cost testing."""
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"video_mock_{uuid.uuid4().hex}.mp4")
    ffmpeg_bin = get_ffmpeg_binary()
    safe_title = scene_title.replace("'", "").replace(":", " -")[:40]
    
    cmd = [
        ffmpeg_bin, "-y",
        "-f", "lavfi",
        "-i", f"color=c={color_hex}:s=720x1280:d={duration}:r=30",
        "-vf", f"drawtext=text='{safe_title}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    try:
        def _run_ffmpeg():
            return subprocess.run(cmd, capture_output=True)

        proc = await asyncio.to_thread(_run_ffmpeg)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        else:
            stderr_str = proc.stderr.decode('utf-8', errors='replace')
            logger.warning(f"FFmpeg synthetic mock generation non-zero exit: {stderr_str}")
    except Exception as e:
        logger.warning(f"Failed to generate synthetic mock MP4 with ffmpeg: {e}")
        
    with open(output_path, 'wb') as f:
        f.write(b"mock_video_data")
    return output_path

async def _mock_generate_multi_clips(count: int = 3, scenes: list[str] = None) -> list[str]:
    """Generates a list of distinct mock clips for offline and zero-cost testing."""
    colors = ["0x1e1b4b", "0x0f172a", "0x064e3b", "0x3b0764"]
    clips = []
    num_scenes = len(scenes) if scenes else count
    for i in range(num_scenes):
        c = colors[i % len(colors)]
        title = scenes[i] if scenes and i < len(scenes) else f"Scene {i+1}"
        clip = await _mock_generate_video(color_hex=c, duration=5, scene_title=title)
        clips.append(clip)
    return clips

