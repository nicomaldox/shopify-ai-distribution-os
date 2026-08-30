import os
import uuid
import logging
from openai import AsyncOpenAI
import tempfile
import asyncio

logger = logging.getLogger(__name__)

async def generate_audio(narration_text: str) -> str:
    """
    Generates TTS audio from the narration_text using OpenAI's TTS API.
    Returns the file path to the generated mp3 file.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not found. Using mock audio generation.")
        return await _mock_generate_audio()
        
    client = AsyncOpenAI(api_key=api_key)
    
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"audio_{uuid.uuid4().hex}.mp3")
    
    logger.info(f"Generating audio voiceover (Length: {len(narration_text)} chars)")
    
    try:
        response = await client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=narration_text
        )
        
        await response.stream_to_file(output_path)
        logger.info(f"Audio successfully saved to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to generate audio: {e}")
        raise

async def _mock_generate_audio() -> str:
    await asyncio.sleep(1)
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"audio_mock_{uuid.uuid4().hex}.mp3")
    with open(output_path, 'wb') as f:
        f.write(b"mock_audio_data")
    return output_path
