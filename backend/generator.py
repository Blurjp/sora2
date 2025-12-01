"""
WAN 2.2 Video Generator Wrapper
"""
import asyncio
import os
import re
import logging
from pathlib import Path
from typing import Optional, Dict
import time
import gc

import torch
from PIL import Image

from .config import (
    OUTPUT_DIR,
    TEMP_DIR,
    FRAMES_PER_SECOND,
    DEFAULT_NUM_STEPS,
    DEFAULT_GUIDANCE,
    DEFAULT_GUIDANCE_IMG,
    WAN_MODEL_ID,
    WAN_MODEL_VARIANT,
    WAN_WIDTH,
    WAN_HEIGHT,
    WAN_ENABLE_MODEL_CPU_OFFLOAD,
    WAN_ENABLE_VAE_SLICING,
    WAN_ENABLE_VAE_TILING,
    WAN_TORCH_DTYPE,
)

logger = logging.getLogger(__name__)

# Enable verbose logging with environment variable
VERBOSE_GENERATION_LOGS = os.environ.get("VERBOSE_GENERATION_LOGS", "false").lower() == "true"


class VideoGenerator:
    """Wrapper for WAN 2.2 video generation using diffusers"""

    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self._generation_lock = asyncio.Lock()
        self._current_task: Optional[asyncio.Task] = None
        self._pipe = None
        self._model_loaded = False

        # Determine torch dtype
        if WAN_TORCH_DTYPE == "float16":
            self._dtype = torch.float16
        else:
            self._dtype = torch.bfloat16

        logger.info("WAN 2.2 Video Generator initialized")
        logger.info(f"Model ID: {WAN_MODEL_ID}")
        logger.info(f"Resolution: {WAN_WIDTH}x{WAN_HEIGHT}")

    def _load_model(self):
        """Load the WAN model (lazy loading on first use)"""
        if self._model_loaded:
            return

        logger.info(f"Loading WAN 2.2 model: {WAN_MODEL_ID}")
        start_time = time.time()

        try:
            # Determine which pipeline to use based on model ID
            if "I2V" in WAN_MODEL_ID:
                from diffusers import WanImageToVideoPipeline
                self._pipe = WanImageToVideoPipeline.from_pretrained(
                    WAN_MODEL_ID,
                    torch_dtype=self._dtype,
                )
                self._pipeline_type = "i2v"
            elif "TI2V" in WAN_MODEL_ID:
                from diffusers import WanImageToVideoPipeline
                self._pipe = WanImageToVideoPipeline.from_pretrained(
                    WAN_MODEL_ID,
                    torch_dtype=self._dtype,
                )
                self._pipeline_type = "ti2v"
            else:
                from diffusers import WanPipeline
                self._pipe = WanPipeline.from_pretrained(
                    WAN_MODEL_ID,
                    torch_dtype=self._dtype,
                )
                self._pipeline_type = "t2v"

            # Apply memory optimizations
            if WAN_ENABLE_MODEL_CPU_OFFLOAD:
                logger.info("Enabling model CPU offload")
                self._pipe.enable_model_cpu_offload()
            else:
                self._pipe = self._pipe.to("cuda")

            if WAN_ENABLE_VAE_SLICING:
                self._pipe.enable_vae_slicing()

            if WAN_ENABLE_VAE_TILING:
                self._pipe.enable_vae_tiling()

            self._model_loaded = True
            load_time = time.time() - start_time
            logger.info(f"Model loaded successfully in {load_time:.1f}s")

        except Exception as e:
            logger.error(f"Failed to load WAN model: {e}", exc_info=True)
            raise

    def calculate_frames(self, duration_seconds: int) -> int:
        """
        Calculate frame count for WAN
        WAN requires frames in format: 4k+1
        """
        total_frames = duration_seconds * FRAMES_PER_SECOND
        k = (total_frames - 1) // 4
        frames = 4 * k + 1
        return min(max(frames, 17), 81)

    def _enhance_prompt_for_quality(self, prompt: str) -> str:
        """Enhance prompt for better quality"""
        prompt_lower = prompt.lower()
        enhancements = []

        quality_keywords = ['high quality', 'detailed', 'sharp', 'clear', '4k', '8k', 'hd', 'cinematic']
        if not any(kw in prompt_lower for kw in quality_keywords):
            enhancements.append("high quality, cinematic")

        face_keywords = [r'\bface\b', r'\bperson\b', r'\bwoman\b', r'\bman\b', r'\bgirl\b', r'\bboy\b', r'\bpeople\b', r'\bportrait\b']
        if any(re.search(pattern, prompt_lower) for pattern in face_keywords):
            if 'detailed face' not in prompt_lower:
                enhancements.append("detailed facial features")

        if 'smooth' not in prompt_lower and 'fluid' not in prompt_lower:
            enhancements.append("smooth motion")

        if enhancements:
            return f"{prompt}, {', '.join(enhancements)}"
        return prompt

    def is_processing(self) -> bool:
        """Return True while a task is still running."""
        task = self._current_task
        return task is not None and not task.done()

    def start_generation(
        self,
        *,
        video_id: str,
        mode: str,
        image_path: Optional[str],
        prompt: str,
        duration: int,
        aspect_ratio: str,
        motion_score: float,
        num_steps: int,
        guidance: float,
        guidance_img: float,
        face_detail: float = 4.5,
        aesthetic_score: float = 6.5,
        sharpness: float = 1.0,
        negative_prompt: Optional[str] = None,
        face_enhance: bool = True,
        denoise: bool = True,
        temporal_smoothing: bool = True,
        seed: Optional[int] = None,
        refine_prompt: bool = False
    ) -> bool:
        """Launch generation. Returns False if a job is already running."""
        if self.is_processing():
            return False

        self._current_task = asyncio.create_task(
            self.generate_video(
                video_id=video_id,
                mode=mode,
                image_path=image_path,
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                motion_score=motion_score,
                num_steps=num_steps,
                guidance=guidance,
                guidance_img=guidance_img,
                negative_prompt=negative_prompt,
                seed=seed,
                refine_prompt=refine_prompt,
            )
        )

        def _clear_task(_: asyncio.Task):
            self._current_task = None

        self._current_task.add_done_callback(_clear_task)
        return True

    def _get_resolution_for_aspect_ratio(self, aspect_ratio: str) -> tuple:
        """Get width and height for aspect ratio"""
        if "TI2V" in WAN_MODEL_ID:
            if aspect_ratio == "9:16":
                return 704, 1280
            else:
                return 1280, 704
        else:
            if WAN_MODEL_VARIANT == "480P":
                if aspect_ratio == "9:16":
                    return 480, 832
                elif aspect_ratio == "1:1":
                    return 480, 480
                else:
                    return 832, 480
            else:
                if aspect_ratio == "9:16":
                    return 720, 1280
                elif aspect_ratio == "1:1":
                    return 720, 720
                else:
                    return 1280, 720

    async def generate_video(
        self,
        video_id: str,
        mode: str,
        image_path: Optional[str],
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        motion_score: float = 0.5,
        num_steps: int = DEFAULT_NUM_STEPS,
        guidance: float = DEFAULT_GUIDANCE,
        guidance_img: float = DEFAULT_GUIDANCE_IMG,
        face_detail: float = 4.5,
        aesthetic_score: float = 6.5,
        sharpness: float = 1.0,
        negative_prompt: Optional[str] = None,
        face_enhance: bool = True,
        denoise: bool = True,
        temporal_smoothing: bool = True,
        seed: Optional[int] = None,
        refine_prompt: bool = False
    ) -> Dict:
        """
        Generate video using WAN 2.2

        Args:
            video_id: Unique identifier for this generation job
            mode: Generation mode (i2v or t2v)
            image_path: Path to input image (required for i2v)
            prompt: Text prompt for generation
            duration: Video duration in seconds
            aspect_ratio: Video aspect ratio
            motion_score: Motion intensity (0.0-1.0)
            num_steps: Diffusion steps
            guidance: Text guidance strength
            guidance_img: Image guidance strength
            negative_prompt: What to avoid
            seed: Random seed for reproducibility
            refine_prompt: Whether to enhance prompt

        Returns:
            Dictionary with generation results
        """
        async with self._generation_lock:
            try:
                # Enhance prompt if requested or by default
                enhanced_prompt = self._enhance_prompt_for_quality(prompt)
                if enhanced_prompt != prompt:
                    logger.info(f"Enhanced prompt: {enhanced_prompt}")

                # Use negative prompt if provided
                neg_prompt = negative_prompt or "low quality, blurry, distorted, watermark, text, deformed"

                # Log parameters
                logger.info(f"=== Starting {mode.upper()} video generation: {video_id} ===")
                logger.info(f"Parameters:")
                logger.info(f"  - Mode: {mode}")
                if image_path:
                    logger.info(f"  - Image: {image_path}")
                logger.info(f"  - Prompt: {enhanced_prompt}")
                logger.info(f"  - Duration: {duration}s")
                logger.info(f"  - Aspect ratio: {aspect_ratio}")
                logger.info(f"  - Num steps: {num_steps}")
                logger.info(f"  - Guidance: {guidance}")
                logger.info(f"  - Seed: {seed}")

                # Update job status
                self.jobs[video_id] = {
                    "status": "processing",
                    "start_time": time.time(),
                    "progress": 0,
                }

                # Load model if needed
                self._load_model()

                # Calculate frames and resolution
                num_frames = self.calculate_frames(duration)
                width, height = self._get_resolution_for_aspect_ratio(aspect_ratio)
                logger.info(f"Generating {num_frames} frames at {width}x{height}")

                # Prepare output path
                output_path = OUTPUT_DIR / f"{video_id}.mp4"

                # Set up generator for reproducibility
                generator = None
                if seed is not None:
                    generator = torch.Generator(device="cuda").manual_seed(seed)

                start_time = time.time()

                # Handle I2V vs T2V modes
                if mode == "i2v" and image_path:
                    # Image-to-Video mode
                    image = Image.open(image_path).convert("RGB")
                    image = image.resize((width, height), Image.Resampling.LANCZOS)

                    logger.info("Starting WAN I2V inference...")
                    output = self._pipe(
                        image=image,
                        prompt=enhanced_prompt,
                        negative_prompt=neg_prompt,
                        height=height,
                        width=width,
                        num_frames=num_frames,
                        guidance_scale=guidance,
                        num_inference_steps=num_steps,
                        generator=generator,
                    )
                else:
                    # Text-to-Video mode (or I2V without image)
                    logger.info("Starting WAN T2V inference...")
                    if hasattr(self._pipe, 'WanPipeline') or self._pipeline_type == "t2v":
                        output = self._pipe(
                            prompt=enhanced_prompt,
                            negative_prompt=neg_prompt,
                            height=height,
                            width=width,
                            num_frames=num_frames,
                            guidance_scale=guidance,
                            num_inference_steps=num_steps,
                            generator=generator,
                        )
                    else:
                        # TI2V can do T2V without image
                        output = self._pipe(
                            prompt=enhanced_prompt,
                            negative_prompt=neg_prompt,
                            height=height,
                            width=width,
                            num_frames=num_frames,
                            guidance_scale=guidance,
                            num_inference_steps=num_steps,
                            generator=generator,
                        )

                # Get frames and export
                frames = output.frames[0]
                from diffusers.utils import export_to_video
                export_to_video(frames, str(output_path), fps=FRAMES_PER_SECOND)

                # Clear memory
                del output, frames
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                duration_taken = time.time() - start_time

                # Verify output
                if not output_path.exists():
                    logger.error("No video file generated")
                    self.jobs[video_id]["status"] = "failed"
                    return {"success": False, "error": "No video file generated"}

                file_size_kb = output_path.stat().st_size / 1024
                logger.info(f"Generated: {output_path} ({file_size_kb:.1f} KB)")

                # Update job status
                self.jobs[video_id].update({
                    "status": "completed",
                    "progress": 100,
                    "output_path": str(output_path),
                    "duration": duration_taken,
                })

                logger.info(f"Video generated successfully: {video_id} ({duration_taken:.1f}s)")

                return {
                    "success": True,
                    "video_path": str(output_path),
                    "duration": duration_taken,
                }

            except torch.cuda.OutOfMemoryError as e:
                error_msg = f"CUDA out of memory: {str(e)}"
                logger.error(error_msg)
                self.jobs[video_id]["status"] = "failed"
                self.jobs[video_id]["error"] = error_msg
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                return {"success": False, "error": error_msg}

            except Exception as e:
                logger.error(f"Error generating video: {e}", exc_info=True)
                self.jobs[video_id]["status"] = "failed"
                self.jobs[video_id]["error"] = str(e)
                return {"success": False, "error": str(e)}

    def get_job_status(self, video_id: str) -> Optional[Dict]:
        """Get status of a generation job"""
        return self.jobs.get(video_id)

    def cleanup_old_files(self, hours: int = 24):
        """Clean up old generated videos"""
        import time
        cutoff_time = time.time() - (hours * 3600)

        for file_path in OUTPUT_DIR.glob("*.mp4"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    logger.info(f"Cleaned up old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error cleaning up {file_path}: {e}")


# Global generator instance
generator = VideoGenerator()
