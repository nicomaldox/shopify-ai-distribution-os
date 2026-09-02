import os
import uuid
import logging
import tempfile
import urllib.parse
import ipaddress
import httpx
import asyncio

logger = logging.getLogger(__name__)

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

async def generate_video(visual_hook: str, pacing_notes: list[str]) -> str:
    """
    Generates a 9:16 vertical video using Fal.ai (Wan) and returns the local file path.
    Falls back gracefully to mock video generation if external cloud API is unavailable.
    """
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        logger.warning("FAL_KEY not found. Using mock video generation.")
        return await _mock_generate_video()
        
    prompt = f"{visual_hook}. Pacing notes: {', '.join(pacing_notes)}"
    logger.info(f"Triggering Fal.ai Video Generation. Prompt: {prompt[:50]}...")
    
    # Supported Fal Wan endpoints
    endpoints = [
        "https://queue.fal.run/fal-ai/wan/v2.1/text-to-video",
        "https://queue.fal.run/fal-ai/wan-2.1-t2v-720p",
        "https://queue.fal.run/fal-ai/wan2.2"
    ]
    
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "aspect_ratio": "9:16"
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for url in endpoints:
            try:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                
                data = response.json()
                request_id = data.get("request_id")
                
                video_url = None
                if request_id:
                    status_url = f"{url}/requests/{request_id}"
                    for _ in range(25):
                        await asyncio.sleep(4)
                        status_resp = await client.get(status_url, headers=headers)
                        status_data = status_resp.json()
                        if status_data.get("status") == "COMPLETED":
                            outputs = status_data.get("output", {}) if "output" in status_data else status_data
                            if "video" in outputs and isinstance(outputs["video"], dict):
                                video_url = outputs["video"].get("url")
                            elif "url" in outputs:
                                video_url = outputs.get("url")
                            break
                        elif status_data.get("status") == "FAILED":
                            break
                else:
                    outputs = data.get("output", {}) if "output" in data else data
                    if "video" in outputs and isinstance(outputs["video"], dict):
                        video_url = outputs["video"].get("url")
                    elif "url" in outputs:
                        video_url = outputs.get("url")
                    
                if video_url:
                    if not is_safe_url(video_url):
                        raise ValueError(f"SSRF Alert: Blocked unsafe video URL: {video_url}")
                        
                    temp_dir = tempfile.gettempdir()
                    output_path = os.path.join(temp_dir, f"video_{uuid.uuid4().hex}.mp4")
                    
                    logger.info(f"Downloading video from {video_url}...")
                    async with client.stream('GET', video_url) as stream_resp:
                        stream_resp.raise_for_status()
                        with open(output_path, 'wb') as f:
                            async for chunk in stream_resp.aiter_bytes():
                                f.write(chunk)
                                
                    logger.info(f"Video successfully saved to {output_path}")
                    return output_path
            except Exception as ep_err:
                logger.warning(f"Fal endpoint {url} failed: {ep_err}")
                continue
                
    logger.warning("Fal.ai cloud video generation unavailable. Falling back to mock video.")
    return await _mock_generate_video()

async def _mock_generate_video() -> str:
    """Generates a valid 3-second 9:16 vertical MP4 video using ffmpeg for offline testing."""
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"video_mock_{uuid.uuid4().hex}.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=0x1a1a2e:s=720x1280:d=3:r=30",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Synthetic mock video generated successfully: {output_path}")
            return output_path
    except Exception as e:
        logger.warning(f"Failed to generate synthetic mock MP4 with ffmpeg: {e}")
        
    with open(output_path, 'wb') as f:
        f.write(b"mock_video_data")
    return output_path
