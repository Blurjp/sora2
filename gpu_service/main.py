"""
GPU Service - Minimal API for video generation on remote GPU
Runs on Lambda Labs or other GPU instances
"""
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import (
    HOST, PORT, API_KEY, TEMP_DIR, OUTPUT_DIR,
    DEFAULT_NUM_STEPS, MIN_NUM_STEPS, MAX_NUM_STEPS,
    DEFAULT_GUIDANCE, MIN_GUIDANCE, MAX_GUIDANCE,
    DEFAULT_GUIDANCE_IMG, MIN_GUIDANCE_IMG, MAX_GUIDANCE_IMG
)
from .generator import generator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Open-Sora GPU Service",
    description="Remote video generation service",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Starting Open-Sora GPU Service")

    # Auto-fix Open-Sora config on startup
    from .opensora_config_fixer import fix_opensora_config
    fix_opensora_config()

    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Temp directory: {TEMP_DIR}")


# Security: Optional API key authentication
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key if configured"""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key


# Response models
class GenerateResponse(BaseModel):
    video_id: str
    status: str
    message: str


class StatusResponse(BaseModel):
    status: str
    video_id: str
    message: Optional[str] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Open-Sora GPU Service",
        "status": "running",
        "processing": generator.is_processing()
    }


@app.get("/api/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "gpu_busy": generator.is_processing(),
        "opensora_path": str(generator.opensora_path),
        "opensora_exists": generator.opensora_path.exists()
    }


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_video(
    image: UploadFile = File(..., description="Input image file"),
    prompt: str = Form(..., description="Text prompt for video generation"),
    duration: int = Form(15, description="Video duration in seconds (5-30)"),
    aspect_ratio: str = Form("16:9", description="Video aspect ratio"),
    motion_score: float = Form(0.5, description="Motion intensity (0.0-1.0)"),
    num_steps: int = Form(DEFAULT_NUM_STEPS, description=f"Diffusion steps ({MIN_NUM_STEPS}-{MAX_NUM_STEPS})"),
    guidance: float = Form(DEFAULT_GUIDANCE, description=f"Text guidance ({MIN_GUIDANCE}-{MAX_GUIDANCE})"),
    guidance_img: float = Form(DEFAULT_GUIDANCE_IMG, description=f"Image guidance ({MIN_GUIDANCE_IMG}-{MAX_GUIDANCE_IMG})"),
    seed: Optional[int] = Form(None, description="Random seed"),
    refine_prompt: bool = Form(False, description="Refine prompt with AI"),
    api_key: str = Depends(verify_api_key)
):
    """
    Generate a video from an image and text prompt

    This endpoint accepts an image and parameters, then generates a video.
    Only one generation can run at a time.
    """
    try:
        # Check if already processing
        if generator.is_processing():
            raise HTTPException(
                status_code=429,
                detail="GPU is busy. Please wait for current generation to complete."
            )

        # Validate duration
        if not (5 <= duration <= 30):
            raise HTTPException(
                status_code=400,
                detail="Duration must be between 5 and 30 seconds"
            )

        # Validate advanced parameters
        if not (MIN_NUM_STEPS <= num_steps <= MAX_NUM_STEPS):
            raise HTTPException(
                status_code=400,
                detail=f"num_steps must be between {MIN_NUM_STEPS} and {MAX_NUM_STEPS}"
            )

        if not (MIN_GUIDANCE <= guidance <= MAX_GUIDANCE):
            raise HTTPException(
                status_code=400,
                detail=f"guidance must be between {MIN_GUIDANCE} and {MAX_GUIDANCE}"
            )

        if not (MIN_GUIDANCE_IMG <= guidance_img <= MAX_GUIDANCE_IMG):
            raise HTTPException(
                status_code=400,
                detail=f"guidance_img must be between {MIN_GUIDANCE_IMG} and {MAX_GUIDANCE_IMG}"
            )

        # Generate unique video ID
        video_id = str(uuid.uuid4())

        # Save uploaded image
        file_ext = Path(image.filename).suffix.lower()
        image_path = TEMP_DIR / f"{video_id}{file_ext}"

        content = await image.read()
        with open(image_path, "wb") as f:
            f.write(content)

        logger.info(f"Received generation request: {video_id}")
        logger.info(f"Prompt: {prompt[:100]}...")

        # Start generation in background
        asyncio.create_task(
            generator.generate_video(
                video_id=video_id,
                image_path=str(image_path),
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                motion_score=motion_score,
                num_steps=num_steps,
                guidance=guidance,
                guidance_img=guidance_img,
                seed=seed,
                refine_prompt=refine_prompt
            )
        )

        return GenerateResponse(
            video_id=video_id,
            status="processing",
            message="Video generation started"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{video_id}", response_model=StatusResponse)
async def check_status(video_id: str):
    """
    Check if a video generation is complete

    Returns whether the video file exists and is ready for download
    """
    try:
        output_path = OUTPUT_DIR / f"{video_id}.mp4"

        if output_path.exists():
            return StatusResponse(
                status="completed",
                video_id=video_id,
                message="Video generation completed"
            )
        elif generator.is_processing():
            return StatusResponse(
                status="processing",
                video_id=video_id,
                message="Video is being generated"
            )
        else:
            # Check if there's a stored error for this video_id
            error = generator.get_error(video_id)
            if error:
                return StatusResponse(
                    status="failed",
                    video_id=video_id,
                    message="Video generation failed",
                    error=error
                )
            else:
                return StatusResponse(
                    status="not_found",
                    video_id=video_id,
                    message="Video not found"
                )

    except Exception as e:
        logger.error(f"Error checking status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{video_id}")
async def download_video(video_id: str):
    """
    Download the generated video file
    """
    try:
        output_path = OUTPUT_DIR / f"{video_id}.mp4"

        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Video not found")

        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename=f"{video_id}.mp4"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/video/{video_id}")
async def delete_video(
    video_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Delete a generated video (requires API key)
    """
    try:
        output_path = OUTPUT_DIR / f"{video_id}.mp4"

        if output_path.exists():
            output_path.unlink()
            return {"message": "Video deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Video not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Run the GPU service"""
    import uvicorn

    logger.info(f"Starting GPU service on {HOST}:{PORT}")
    logger.info(f"API Key protection: {'enabled' if API_KEY else 'disabled'}")

    uvicorn.run(
        "gpu_service.main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
