"""
WAN 2.2 Video Generator
Uses HuggingFace Diffusers for video generation
"""
import asyncio
import os
import logging
import re
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
        self._generation_lock = asyncio.Lock()
        self._current_task: Optional[asyncio.Task] = None
        self._errors: Dict[str, str] = {}
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
        logger.info(f"Torch dtype: {WAN_TORCH_DTYPE}")

    def _load_model(self):
        """Load the WAN model (lazy loading on first use)"""
        if self._model_loaded:
            return

        logger.info(f"Loading WAN 2.2 model: {WAN_MODEL_ID}")
        start_time = time.time()

        try:
            # Determine which pipeline to use based on model ID
            # Disable safety checker for unrestricted generation
            if "I2V" in WAN_MODEL_ID:
                from diffusers import WanImageToVideoPipeline
                self._pipe = WanImageToVideoPipeline.from_pretrained(
                    WAN_MODEL_ID,
                    torch_dtype=self._dtype,
                    safety_checker=None,
                    requires_safety_checker=False,
                )
                self._pipeline_type = "i2v"
            elif "TI2V" in WAN_MODEL_ID:
                # TI2V supports both T2V and I2V
                from diffusers import WanImageToVideoPipeline
                self._pipe = WanImageToVideoPipeline.from_pretrained(
                    WAN_MODEL_ID,
                    torch_dtype=self._dtype,
                    safety_checker=None,
                    requires_safety_checker=False,
                )
                self._pipeline_type = "ti2v"
            else:
                # Default to T2V
                from diffusers import WanPipeline
                self._pipe = WanPipeline.from_pretrained(
                    WAN_MODEL_ID,
                    torch_dtype=self._dtype,
                    safety_checker=None,
                    requires_safety_checker=False,
                )
                self._pipeline_type = "t2v"

            # Explicitly disable any safety components
            if hasattr(self._pipe, 'safety_checker'):
                self._pipe.safety_checker = None
            if hasattr(self._pipe, 'feature_extractor'):
                self._pipe.feature_extractor = None

            # Apply memory optimizations
            if WAN_ENABLE_MODEL_CPU_OFFLOAD:
                logger.info("Enabling model CPU offload for memory optimization")
                self._pipe.enable_model_cpu_offload()
            else:
                self._pipe = self._pipe.to("cuda")

            if WAN_ENABLE_VAE_SLICING:
                logger.info("Enabling VAE slicing")
                self._pipe.enable_vae_slicing()

            if WAN_ENABLE_VAE_TILING:
                logger.info("Enabling VAE tiling")
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
        # Round to nearest 4k+1 format
        k = (total_frames - 1) // 4
        frames = 4 * k + 1
        # WAN typically works best with 81 frames (5s at 16fps)
        return min(max(frames, 17), 81)

    def _enhance_prompt_for_quality(self, prompt: str) -> str:
        """
        Enhance prompt for better quality
        """
        prompt_lower = prompt.lower()
        enhancements = []

        # Add quality keywords if not present
        quality_keywords = ['high quality', 'detailed', 'sharp', 'clear', '4k', '8k', 'hd', 'cinematic']
        if not any(kw in prompt_lower for kw in quality_keywords):
            enhancements.append("high quality, cinematic")

        # Add smooth motion keyword for video quality
        if 'smooth' not in prompt_lower and 'fluid' not in prompt_lower:
            enhancements.append("smooth motion")

        if enhancements:
            return f"{prompt}, {', '.join(enhancements)}"
        return prompt

    def is_processing(self) -> bool:
        """Return True while a generation task is still running."""
        task = self._current_task
        return task is not None and not task.done()

    def get_error(self, video_id: str) -> Optional[str]:
        """Get stored error for a video_id if any"""
        return self._errors.get(video_id)

    def _get_resolution_for_aspect_ratio(self, aspect_ratio: str) -> tuple:
        """Get width and height for aspect ratio"""
        # WAN 2.2 supported resolutions
        if "TI2V" in WAN_MODEL_ID:
            # TI2V-5B: 1280x704 or 704x1280
            if aspect_ratio == "9:16":
                return 704, 1280
            else:  # 16:9 or 1:1
                return 1280, 704
        else:
            # I2V-A14B: 1280x720 or 720x1280 (720P) or 832x480 (480P)
            if WAN_MODEL_VARIANT == "480P":
                if aspect_ratio == "9:16":
                    return 480, 832
                elif aspect_ratio == "1:1":
                    return 480, 480
                else:  # 16:9
                    return 832, 480
            else:  # 720P
                if aspect_ratio == "9:16":
                    return 720, 1280
                elif aspect_ratio == "1:1":
                    return 720, 720
                else:  # 16:9
                    return 1280, 720

    async def generate_video(
        self,
        video_id: str,
        image_path: str,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        motion_score: float = 0.5,
        num_steps: int = DEFAULT_NUM_STEPS,
        guidance: float = DEFAULT_GUIDANCE,
        guidance_img: float = DEFAULT_GUIDANCE_IMG,
        seed: Optional[int] = None,
        refine_prompt: bool = False
    ) -> Dict:
        """
        Generate video using WAN 2.2

        Args:
            video_id: Unique identifier for this generation job
            image_path: Path to input image
            prompt: Text prompt for generation
            duration: Video duration in seconds
            aspect_ratio: Video aspect ratio
            motion_score: Motion intensity (0.0-1.0) - not directly used in WAN
            num_steps: Diffusion steps
            guidance: Text guidance strength
            guidance_img: Image guidance strength (not used in WAN I2V)
            seed: Random seed for reproducibility
            refine_prompt: Whether to enhance prompt

        Returns:
            Dictionary with generation results
        """
        async with self._generation_lock:
            try:
                # Enhance prompt if requested
                if refine_prompt:
                    enhanced_prompt = self._enhance_prompt_for_quality(prompt)
                else:
                    enhanced_prompt = prompt

                if enhanced_prompt != prompt:
                    logger.info(f"Enhanced prompt: {enhanced_prompt}")

                # Log generation parameters
                logger.info(f"=== Starting video generation: {video_id} ===")
                logger.info(f"Parameters:")
                logger.info(f"  - Image: {image_path}")
                logger.info(f"  - Prompt: {enhanced_prompt}")
                logger.info(f"  - Duration: {duration}s")
                logger.info(f"  - Aspect ratio: {aspect_ratio}")
                logger.info(f"  - Num steps: {num_steps}")
                logger.info(f"  - Guidance: {guidance}")
                logger.info(f"  - Seed: {seed}")

                # Load model if not already loaded
                self._load_model()

                # Calculate frames and resolution
                num_frames = self.calculate_frames(duration)
                width, height = self._get_resolution_for_aspect_ratio(aspect_ratio)
                logger.info(f"Generating {num_frames} frames at {width}x{height}")

                # Prepare output path
                output_path = OUTPUT_DIR / f"{video_id}.mp4"

                # Load and process input image
                image = Image.open(image_path).convert("RGB")
                # Resize image to match output resolution
                image = image.resize((width, height), Image.Resampling.LANCZOS)

                # Set up generator for reproducibility
                generator = None
                if seed is not None:
                    generator = torch.Generator(device="cuda").manual_seed(seed)

                start_time = time.time()

                # Run generation - no content restrictions
                logger.info("Starting WAN inference...")
                output = self._pipe(
                    image=image,
                    prompt=enhanced_prompt,
                    negative_prompt="",  # No negative prompt restrictions
                    height=height,
                    width=width,
                    num_frames=num_frames,
                    guidance_scale=guidance,
                    num_inference_steps=num_steps,
                    generator=generator,
                )

                # Get frames from output
                frames = output.frames[0]

                # Export to video
                from diffusers.utils import export_to_video
                export_to_video(frames, str(output_path), fps=FRAMES_PER_SECOND)

                # Clear memory
                del output, frames
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                duration_taken = time.time() - start_time
                logger.info(f"Video generated successfully: {video_id} ({duration_taken:.1f}s)")

                # Verify output file
                if not output_path.exists():
                    error_msg = "Video file was not created"
                    logger.error(error_msg)
                    self._errors[video_id] = error_msg
                    return {"success": False, "error": error_msg}

                file_size_kb = output_path.stat().st_size / 1024
                logger.info(f"Output file: {output_path} ({file_size_kb:.1f} KB)")

                return {
                    "success": True,
                    "video_path": str(output_path),
                    "duration": duration_taken,
                }

            except torch.cuda.OutOfMemoryError as e:
                error_msg = f"CUDA out of memory: {str(e)}"
                logger.error(error_msg)
                self._errors[video_id] = error_msg

                # Try to recover
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                return {"success": False, "error": error_msg}

            except Exception as e:
                error_msg = f"Exception during video generation: {str(e)}"
                logger.error(error_msg, exc_info=True)
                self._errors[video_id] = error_msg
                return {"success": False, "error": error_msg}


# Global generator instance
generator = VideoGenerator()
