"""
FastAPI Backend for Open-Sora Video Generation Service
"""
import logging
import uuid
from pathlib import Path
from typing import Optional
import asyncio
import mimetypes

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .models import (
    GenerateResponse,
    StatusResponse,
    VideoStatus,
    AspectRatio,
)
from .generator import generator
from .remote_generator import remote_generator
from .config import (
    HOST,
    PORT,
    TEMP_DIR,
    OUTPUT_DIR,
    STATIC_DIR,
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_UPLOAD_SIZE,
    CLEANUP_AFTER_HOURS,
    MIN_DURATION,
    MAX_DURATION,
    USE_REMOTE_GPU,
    GPU_SERVICE_URL,
    DEFAULT_NUM_STEPS,
    MIN_NUM_STEPS,
    MAX_NUM_STEPS,
    DEFAULT_GUIDANCE,
    MIN_GUIDANCE,
    MAX_GUIDANCE,
    DEFAULT_GUIDANCE_IMG,
    MIN_GUIDANCE_IMG,
    MAX_GUIDANCE_IMG,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Open-Sora Video Generation API",
    description="Generate high-quality videos from images and text using Open-Sora 2.0",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Select generator based on configuration
active_generator = remote_generator if USE_REMOTE_GPU else generator

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Starting Open-Sora Video Generation Service")
    logger.info(f"Mode: {'Remote GPU' if USE_REMOTE_GPU else 'Local GPU'}")

    # Auto-fix Open-Sora config on startup (local mode only)
    if not USE_REMOTE_GPU:
        from .opensora_config_fixer import fix_opensora_config
        fix_opensora_config()

    if USE_REMOTE_GPU:
        logger.info(f"GPU Service URL: {GPU_SERVICE_URL}")
        # Check GPU service health
        health = await remote_generator.health_check()
        if health.get("status") == "healthy":
            logger.info("GPU service is healthy and ready")
        else:
            logger.warning(f"GPU service health check failed: {health}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Temp directory: {TEMP_DIR}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down service")
    if USE_REMOTE_GPU:
        await remote_generator.cleanup()


@app.get("/")
async def root():
    """Serve the main HTML page"""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Open-Sora Video Generation Service API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "open-sora-video-gen"}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_video(
    background_tasks: BackgroundTasks,
    mode: str = Form("i2v", description="Generation mode: i2v (image-to-video) or t2v (text-to-video)"),
    image: Optional[UploadFile] = File(None, description="Input image file (required for i2v mode)"),
    prompt: str = Form(..., description="Text prompt for video generation"),
    duration: int = Form(15, description=f"Video duration in seconds ({MIN_DURATION}-{MAX_DURATION})"),
    aspect_ratio: str = Form("16:9", description="Video aspect ratio"),
    motion_score: float = Form(0.5, description="Motion intensity (0.0-1.0)"),
    num_steps: int = Form(DEFAULT_NUM_STEPS, description=f"Diffusion steps ({MIN_NUM_STEPS}-{MAX_NUM_STEPS}, more=better quality)"),
    guidance: float = Form(DEFAULT_GUIDANCE, description=f"Text guidance ({MIN_GUIDANCE}-{MAX_GUIDANCE}, higher=follows prompt more)"),
    guidance_img: float = Form(DEFAULT_GUIDANCE_IMG, description=f"Image guidance ({MIN_GUIDANCE_IMG}-{MAX_GUIDANCE_IMG}, lower=more freedom)"),
    face_detail: float = Form(4.5, description="Face detail level (0.5-10, higher=sharper faces)"),
    aesthetic_score: float = Form(6.5, description="Aesthetic quality (4-9.5, higher=better visual appeal)"),
    sharpness: float = Form(1.0, description="Sharpness level (0=soft, 1=natural, 2=sharp)"),
    negative_prompt: Optional[str] = Form(None, description="What to avoid in the video"),
    face_enhance: bool = Form(True, description="Enable face enhancement"),
    denoise: bool = Form(True, description="Enable denoising"),
    temporal_smoothing: bool = Form(True, description="Enable temporal smoothing"),
    seed: Optional[int] = Form(None, description="Random seed"),
    refine_prompt: bool = Form(False, description="Refine prompt with AI")
):
    """
    Generate a video from an image and text prompt

    - **image**: Input image file (PNG, JPG, WEBP)
    - **prompt**: Text description for the video
    - **duration**: Video length in seconds
    - **aspect_ratio**: Video dimensions (16:9, 9:16, 1:1, 2.39:1)
    - **motion_score**: How much motion to apply (0.0-1.0)
    - **num_steps**: Diffusion sampling steps (more = better quality but slower)
    - **guidance**: Text guidance strength (higher = follows prompt description more closely)
    - **guidance_img**: Image guidance strength (lower = more creative freedom from reference image)
    - **seed**: Random seed for reproducibility (optional)
    - **refine_prompt**: Use AI to enhance the prompt (optional)
    """
    try:
        # Validate mode
        if mode not in ["i2v", "t2v"]:
            raise HTTPException(
                status_code=400,
                detail="mode must be either 'i2v' or 't2v'"
            )

        # Check if a generation is already in progress
        if active_generator.is_processing():
            raise HTTPException(
                status_code=429,
                detail="A video generation is already in progress. Please wait for it to complete."
            )

        # For i2v mode, image is required
        if mode == "i2v" and not image:
            raise HTTPException(
                status_code=400,
                detail="Image is required for image-to-video mode"
            )

        # Handle image upload for i2v mode
        image_path = None
        if mode == "i2v" and image:
            # Validate image file
            file_ext = Path(image.filename).suffix.lower()
            if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
                )

            # Generate unique video ID
            video_id = str(uuid.uuid4())

            # Save uploaded image
            image_path = TEMP_DIR / f"{video_id}{file_ext}"
            content = await image.read()

            # Check file size
            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE // 1024 // 1024}MB"
                )

            with open(image_path, "wb") as f:
                f.write(content)
        else:
            # T2V mode - no image needed
            video_id = str(uuid.uuid4())

        # Validate duration
        if not (MIN_DURATION <= duration <= MAX_DURATION):
            raise HTTPException(
                status_code=400,
                detail=f"Duration must be between {MIN_DURATION} and {MAX_DURATION} seconds"
            )

        # Validate num_steps
        if not (MIN_NUM_STEPS <= num_steps <= MAX_NUM_STEPS):
            raise HTTPException(
                status_code=400,
                detail=f"num_steps must be between {MIN_NUM_STEPS} and {MAX_NUM_STEPS}"
            )

        # Validate guidance
        if not (MIN_GUIDANCE <= guidance <= MAX_GUIDANCE):
            raise HTTPException(
                status_code=400,
                detail=f"guidance must be between {MIN_GUIDANCE} and {MAX_GUIDANCE}"
            )

        # Validate guidance_img
        if not (MIN_GUIDANCE_IMG <= guidance_img <= MAX_GUIDANCE_IMG):
            raise HTTPException(
                status_code=400,
                detail=f"guidance_img must be between {MIN_GUIDANCE_IMG} and {MAX_GUIDANCE_IMG}"
            )

        logger.info(f"Received {mode.upper()} generation request: {video_id}")
        logger.info(f"Prompt: {prompt[:100]}...")

        # Start generation (returns False only if someone else snuck in)
        started = active_generator.start_generation(
            video_id=video_id,
            mode=mode,
            image_path=str(image_path) if image_path else None,
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            motion_score=motion_score,
            num_steps=num_steps,
            guidance=guidance,
            guidance_img=guidance_img,
            face_detail=face_detail,
            aesthetic_score=aesthetic_score,
            sharpness=sharpness,
            negative_prompt=negative_prompt,
            face_enhance=face_enhance,
            denoise=denoise,
            temporal_smoothing=temporal_smoothing,
            seed=seed,
            refine_prompt=refine_prompt,
        )

        if not started:
            raise HTTPException(
                status_code=429,
                detail="A video generation is already in progress. Please wait for it to complete."
            )

        return GenerateResponse(
            video_id=video_id,
            status=VideoStatus.PROCESSING,
            message="Video generation started. Check status with /api/status/{video_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{video_id}", response_model=StatusResponse)
async def get_status(video_id: str):
    """
    Check the status of a video generation job

    - **video_id**: The unique video identifier returned from /api/generate
    """
    job = active_generator.get_job_status(video_id)

    if not job:
        raise HTTPException(status_code=404, detail="Video not found")

    status = VideoStatus(job["status"])
    response = StatusResponse(
        video_id=video_id,
        status=status,
        progress=job.get("progress"),
        error=job.get("error")
    )

    if status == VideoStatus.COMPLETED:
        response.video_url = f"/api/download/{video_id}"

    return response


@app.get("/api/download/{video_id}")
async def download_video(video_id: str):
    """
    Download a generated video

    - **video_id**: The unique video identifier
    """
    video_path = OUTPUT_DIR / f"{video_id}.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"{video_id}.mp4"
    )


@app.delete("/api/video/{video_id}")
async def delete_video(video_id: str):
    """
    Delete a generated video

    - **video_id**: The unique video identifier
    """
    video_path = OUTPUT_DIR / f"{video_id}.mp4"
    image_path = TEMP_DIR / f"{video_id}"

    deleted = False

    if video_path.exists():
        video_path.unlink()
        deleted = True

    # Clean up temp image files
    for temp_file in TEMP_DIR.glob(f"{video_id}.*"):
        temp_file.unlink()
        deleted = True

    if not deleted:
        raise HTTPException(status_code=404, detail="Video not found")

    return {"message": "Video deleted successfully"}


@app.post("/api/cleanup")
async def cleanup_old_videos():
    """
    Clean up videos older than 24 hours (admin endpoint)
    """
    try:
        generator.cleanup_old_files(hours=CLEANUP_AFTER_HOURS)
        return {"message": f"Cleaned up videos older than {CLEANUP_AFTER_HOURS} hours"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Run the server"""
    logger.info(f"Starting server on {HOST}:{PORT}")
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
