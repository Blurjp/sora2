"""
Open-Sora 2.0 Video Generator
Simplified version for GPU service only
"""
import subprocess
import asyncio
import os
import logging
from pathlib import Path
from typing import Optional, Dict
import time
import re

from .config import (
    OPENSORA_PATH,
    OUTPUT_DIR,
    TEMP_DIR,
    FRAMES_PER_SECOND,
    MODEL_CONFIG_PATH,
    CHECKPOINT_PATH,
    DEFAULT_NUM_STEPS,
    DEFAULT_GUIDANCE,
    DEFAULT_GUIDANCE_IMG,
)

logger = logging.getLogger(__name__)

# Enable verbose logging with environment variable
VERBOSE_GENERATION_LOGS = os.environ.get("VERBOSE_GENERATION_LOGS", "false").lower() == "true"


class VideoGenerator:
    """Wrapper for Open-Sora 2.0 video generation"""

    def __init__(self):
        self.opensora_path = Path(OPENSORA_PATH)
        self._generation_lock = asyncio.Lock()
        self._current_task: Optional[asyncio.Task] = None
        # Track errors for each video_id
        self._errors: Dict[str, str] = {}

        # MAXIMUM GPU PERFORMANCE: Set high-performance CUDA environment
        # Note: These are set globally and will be used by all generations
        logger.info("Initializing GPU service with MAXIMUM performance settings")
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        os.environ.setdefault("CUDNN_BENCHMARK", "1")
        os.environ.setdefault("TORCH_CUDNN_V8_API_ENABLED", "1")
        os.environ.setdefault("TORCH_ALLOW_TF32", "1")

    def calculate_frames(self, duration_seconds: int) -> int:
        """
        Calculate frame count for Open-Sora
        Open-Sora requires frames in format: 4k+1 and less than 129
        """
        total_frames = duration_seconds * FRAMES_PER_SECOND
        # Round to nearest 4k+1 format
        k = (total_frames - 1) // 4
        frames = 4 * k + 1
        # Ensure within limits
        return min(frames, 125)  # Max 125 (4*31+1)

    def _enhance_prompt_for_quality(self, prompt: str) -> str:
        """
        Enhance prompt for better quality and face preservation
        Adds quality-improving keywords if not already present
        """
        prompt_lower = prompt.lower()
        enhancements = []

        # Add quality keywords if not present
        quality_keywords = ['high quality', 'detailed', 'sharp', 'clear', '4k', '8k', 'hd']
        if not any(kw in prompt_lower for kw in quality_keywords):
            enhancements.append("high quality")

        # Add face preservation keywords if face/person detected (whole word match)
        face_keywords = [r'\bface\b', r'\bperson\b', r'\bwoman\b', r'\bman\b', r'\bgirl\b', r'\bboy\b', r'\bpeople\b', r'\bportrait\b']
        if any(re.search(pattern, prompt_lower) for pattern in face_keywords):
            if 'detailed face' not in prompt_lower and 'clear face' not in prompt_lower:
                enhancements.append("detailed facial features")

        # Add smooth motion keyword for video quality
        if 'smooth' not in prompt_lower and 'fluid' not in prompt_lower:
            enhancements.append("smooth motion")

        if enhancements:
            return f"{prompt}, {', '.join(enhancements)}"
        return prompt

    def is_processing(self) -> bool:
        """Return True while a torchrun task is still running."""
        task = self._current_task
        return task is not None and not task.done()

    def get_error(self, video_id: str) -> Optional[str]:
        """Get stored error for a video_id if any"""
        return self._errors.get(video_id)

    def _patch_opensora_memory(self, config_filename: str) -> None:
        """Best-effort patch: enable temporal tiling in the VAE to lower VRAM.

        Modifies the Open-Sora inference config in-place on the GPU host.
        Safe to call multiple times; idempotent changes only.
        """
        cfg_path = self.opensora_path / config_filename
        try:
            text = cfg_path.read_text()
        except Exception:
            return

        original = text

        # Ensure ae dict has use_temporal_tiling=True
        # 1) If an explicit False is present, flip to True
        text = re.sub(
            r"(use_temporal_tiling\s*:\s*)False",
            r"\1True",
            text,
        )

        # 2) If key missing inside ae dict, insert it next to use_spatial_tiling
        def _inject_temporal_tiling(match: re.Match) -> str:
            body = match.group(1)
            if re.search(r"use_temporal_tiling\s*:\s*", body):
                return match.group(0)  # already present
            # try to place after use_spatial_tiling if present
            body2 = re.sub(
                r"(use_spatial_tiling\s*:\s*True\s*,?)",
                r"\1\n        'use_temporal_tiling': True,",
                body,
                count=1,
            )
            if body2 == body:
                # otherwise append near the start
                body2 = re.sub(
                    r"^",
                    "'use_temporal_tiling': True,\n        ",
                    body,
                    count=1,
                )
            return f"ae = dict(\n    {body2}\n)"

        text = re.sub(
            r"ae\s*=\s*dict\s*\(\n\s*(.*?)\n\s*\)",
            _inject_temporal_tiling,
            text,
            flags=re.DOTALL,
        )

        if text != original:
            try:
                cfg_path.write_text(text)
            except Exception:
                pass

    async def _run_generation(self, cmd: list, extra_env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        env = os.environ.copy()

        # MAXIMUM GPU PERFORMANCE SETTINGS
        # These environment variables optimize CUDA for maximum throughput
        perf_env = {
            # PyTorch optimizations
            "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",  # Better memory management
            "TORCH_CUDNN_V8_API_ENABLED": "1",  # Enable cuDNN v8 optimizations
            "CUDA_LAUNCH_BLOCKING": "0",  # Async kernel launches for speed

            # cuDNN optimizations
            "CUDNN_BENCHMARK": "1",  # Auto-tune for best performance
            "CUDNN_DETERMINISTIC": "0",  # Allow non-deterministic for speed

            # TensorFloat-32 for speed (compatible with A100, A6000, etc.)
            "TORCH_ALLOW_TF32_CUBLAS_OVERRIDE": "1",
            "TORCH_ALLOW_TF32": "1",

            # Disable CPU fallback to force GPU usage
            "CUDA_VISIBLE_DEVICES": "0",  # Use first GPU

            # Memory optimization
            "PYTORCH_NO_CUDA_MEMORY_CACHING": "0",  # Enable caching for speed
        }
        env.update(perf_env)

        if extra_env:
            env.update(extra_env)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.opensora_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await process.communicate()
        return subprocess.CompletedProcess(cmd, process.returncode, stdout, stderr)

    async def generate_video(
        self,
        video_id: str,
        image_path: str,
        prompt: str,
        duration: int = 15,
        aspect_ratio: str = "16:9",
        motion_score: float = 0.5,
        num_steps: int = DEFAULT_NUM_STEPS,
        guidance: float = DEFAULT_GUIDANCE,
        guidance_img: float = DEFAULT_GUIDANCE_IMG,
        seed: Optional[int] = None,
        refine_prompt: bool = False
    ) -> Dict:
        """
        Generate video using Open-Sora 2.0

        Args:
            video_id: Unique identifier for this generation job
            image_path: Path to input image
            prompt: Text prompt for generation
            duration: Video duration in seconds
            aspect_ratio: Video aspect ratio
            motion_score: Motion intensity (0.0-1.0)
            seed: Random seed for reproducibility
            refine_prompt: Whether to refine prompt with AI

        Returns:
            Dictionary with generation results
        """
        # Acquire lock to prevent concurrent generations
        async with self._generation_lock:
            try:
                # Enhance prompt for better quality and face preservation
                enhanced_prompt = self._enhance_prompt_for_quality(prompt)
                if enhanced_prompt != prompt:
                    logger.info(f"Enhanced prompt for quality: {enhanced_prompt}")

                # Log generation parameters
                logger.info(f"=== Starting video generation: {video_id} ===")
                logger.info(f"Parameters:")
                logger.info(f"  - Image: {image_path}")
                logger.info(f"  - Prompt: {enhanced_prompt}")
                logger.info(f"  - Duration: {duration}s")
                logger.info(f"  - Aspect ratio: {aspect_ratio}")
                logger.info(f"  - Motion score: {motion_score}")
                logger.info(f"  - Num steps: {num_steps}")
                logger.info(f"  - Guidance: {guidance}")
                logger.info(f"  - Guidance img: {guidance_img}")
                logger.info(f"  - Seed: {seed}")
                logger.info(f"  - Refine prompt: {refine_prompt}")

                # Calculate frames
                num_frames = self.calculate_frames(duration)
                logger.info(f"Generating {num_frames} frames for {duration}s video")

                # Create unique output directory for this job to avoid file conflicts
                job_output_dir = OUTPUT_DIR / video_id
                job_output_dir.mkdir(exist_ok=True)

                # Prepare output path
                output_path = OUTPUT_DIR / f"{video_id}.mp4"

                # Use config file directly from Open-Sora directory
                # Don't copy it - copying breaks _base_ imports in mmengine
                config_file_path = Path(self.opensora_path) / MODEL_CONFIG_PATH

                logger.info(f"Using config: {MODEL_CONFIG_PATH} with custom parameters")
                logger.info(f"Quality settings: steps={num_steps}, guidance={guidance}, guidance_img={guidance_img}")

                # Build command - use config from Open-Sora directory
                # Pass quality parameters via command line to override config defaults
                # IMPORTANT: Removed --offload for MAXIMUM GPU utilization
                # Offloading moves models between CPU/GPU which reduces performance
                # Only enable offload if you have low VRAM (<24GB)
                cmd = [
                    "torchrun",
                    "--nproc_per_node", "1",
                    "--standalone",
                    "scripts/diffusion/inference.py",
                    str(config_file_path),
                    "--num-sampling-steps", str(num_steps),
                    "--cfg-scale", str(guidance),
                    "--cond_type", "i2v_head",
                    "--ref", str(image_path),
                    "--prompt", enhanced_prompt,  # Use enhanced prompt
                    "--num_frames", str(num_frames),
                    "--aspect_ratio", aspect_ratio,
                    "--motion-score", str(motion_score),
                    "--save_dir", str(job_output_dir),
                    # --offload removed for full GPU utilization
                ]

                # Only add --ckpt if explicitly set via environment variable
                # Otherwise, let the config file's from_pretrained handle model loading
                if CHECKPOINT_PATH and os.environ.get("CHECKPOINT_PATH"):
                    cmd.extend(["--ckpt", CHECKPOINT_PATH])

                # Add optional parameters
                if seed is not None:
                    cmd.extend(["--seed", str(seed)])

                if refine_prompt:
                    cmd.append("--refine-prompt")

                logger.info(f"Starting video generation: {video_id}")
                logger.info(f"Working directory: {self.opensora_path}")
                logger.info(f"Command: {' '.join(cmd)}")

                start_time = time.time()

                # Run generation
                result = await self._run_generation(cmd)

                if result.returncode != 0:
                    # Log full stdout/stderr on failure
                    if result.stdout:
                        stdout_text = result.stdout.decode(errors="replace")
                        logger.error(f"=== Generation stdout for {video_id} ===")
                        for line in stdout_text.split('\n'):
                            if line.strip():
                                logger.error(f"STDOUT: {line}")

                    if result.stderr:
                        stderr_text = result.stderr.decode(errors="replace")
                        logger.error(f"=== Generation stderr for {video_id} ===")
                        for line in stderr_text.split('\n'):
                            if line.strip():
                                logger.error(f"STDERR: {line}")
                    err_text = (result.stderr or b"").decode(errors="replace")
                    # Retry strategy on CUDA OOM: reduce frames and tighten allocator split
                    if "CUDA out of memory" in err_text or "torch.OutOfMemoryError" in err_text:
                        logger.warning("CUDA OOM detected. Retrying with fewer frames and allocator tweaks...")
                        # reduce frames to ~75% while preserving 4k+1 pattern
                        reduced = max(int(num_frames * 0.75), 49)
                        k = (reduced - 1) // 4
                        reduced_frames = 4 * k + 1

                        # Rebuild command with fewer frames
                        retry_cmd = list(cmd)
                        if "--num_frames" in retry_cmd:
                            idx = retry_cmd.index("--num_frames")
                            retry_cmd[idx + 1] = str(reduced_frames)

                        retry_env = {"PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True,max_split_size_mb:64"}
                        retry = await self._run_generation(retry_cmd, extra_env=retry_env)
                        if retry.returncode == 0:
                            # Replace outputs to final location as below
                            stdout = retry.stdout
                            stderr = retry.stderr
                        else:
                            error_msg = (retry.stderr or b"").decode(errors="replace") or err_text or "Unknown error"
                            logger.error(f"Generation failed after retry: {error_msg}")
                            self._errors[video_id] = error_msg
                            return {"success": False, "error": error_msg}
                    else:
                        error_msg = err_text or "Unknown error"
                        logger.error(f"Generation failed: {error_msg}")
                        self._errors[video_id] = error_msg
                        return {"success": False, "error": error_msg}

                # Log output for successful runs
                if VERBOSE_GENERATION_LOGS:
                    # Full output when verbose logging is enabled
                    if result.stdout:
                        stdout_text = result.stdout.decode(errors="replace")
                        logger.info(f"Generation stdout (full):\n{stdout_text}")
                    if result.stderr:
                        stderr_text = result.stderr.decode(errors="replace")
                        logger.info(f"Generation stderr (full):\n{stderr_text}")
                else:
                    # Truncated output at debug level by default
                    if result.stdout:
                        stdout_text = result.stdout.decode(errors="replace")
                        logger.debug(f"Generation stdout (last 1000 chars): {stdout_text[-1000:]}")
                    if result.stderr:
                        stderr_text = result.stderr.decode(errors="replace")
                        logger.debug(f"Generation stderr (last 1000 chars): {stderr_text[-1000:]}")

                # Find generated video file in job-specific directory (search recursively)
                generated_files = list(job_output_dir.glob("**/*.mp4"))
                if not generated_files:
                    # Log directory contents for debugging
                    all_files = list(job_output_dir.glob("*"))
                    error_msg = "No video file generated"
                    logger.error(f"{error_msg} in {job_output_dir}")
                    logger.error(f"Directory contents: {[f.name for f in all_files]}")
                    logger.error(f"Directory exists: {job_output_dir.exists()}")

                    # Log last part of stdout/stderr if available
                    if result.stdout:
                        stdout_text = result.stdout.decode(errors="replace")
                        logger.error(f"Last 500 chars of stdout: {stdout_text[-500:]}")
                    if result.stderr:
                        stderr_text = result.stderr.decode(errors="replace")
                        logger.error(f"Last 500 chars of stderr: {stderr_text[-500:]}")

                    self._errors[video_id] = error_msg
                    return {
                        "success": False,
                        "error": error_msg
                    }

                # Get the generated file (should only be one in this directory)
                generated_file = generated_files[0]

                # Log video file properties
                file_size_kb = generated_file.stat().st_size / 1024
                logger.info(f"Generated video found: {generated_file.name}")
                logger.info(f"File size: {file_size_kb:.1f} KB")
                logger.info(f"Full path: {generated_file}")
                logger.info(f"Requested aspect ratio: {aspect_ratio}")

                # Check video properties with ffprobe if available
                try:
                    import subprocess
                    probe_result = subprocess.run(
                        ["ffprobe", "-v", "error", "-show_entries",
                         "format=duration:stream=width,height,nb_frames",
                         "-of", "default=noprint_wrappers=1", str(generated_file)],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if probe_result.returncode == 0:
                        logger.info(f"Video properties:\n{probe_result.stdout}")

                        # Check if aspect ratio matches request
                        width_match = re.search(r'width=(\d+)', probe_result.stdout)
                        height_match = re.search(r'height=(\d+)', probe_result.stdout)
                        if width_match and height_match:
                            actual_width = int(width_match.group(1))
                            actual_height = int(height_match.group(1))
                            actual_ratio = actual_width / actual_height

                            # Calculate expected ratio
                            if aspect_ratio == "16:9":
                                expected_ratio = 16/9
                            elif aspect_ratio == "9:16":
                                expected_ratio = 9/16
                            elif aspect_ratio == "1:1":
                                expected_ratio = 1.0
                            elif aspect_ratio == "2.39:1":
                                expected_ratio = 2.39
                            else:
                                expected_ratio = None

                            if expected_ratio:
                                ratio_diff = abs(actual_ratio - expected_ratio)
                                if ratio_diff > 0.1:
                                    logger.warning(f"Aspect ratio mismatch! Requested: {aspect_ratio} ({expected_ratio:.2f}), Got: {actual_width}x{actual_height} ({actual_ratio:.2f})")
                                else:
                                    logger.info(f"✅ Aspect ratio correct: {aspect_ratio}")
                    else:
                        logger.warning(f"Could not probe video: {probe_result.stderr}")
                except Exception as e:
                    logger.debug(f"ffprobe not available or failed: {e}")

                # Move to final output location
                generated_file.rename(output_path)

                # Clean up job directory
                try:
                    job_output_dir.rmdir()
                except:
                    pass  # Directory not empty or other issue, ignore

                duration_taken = time.time() - start_time
                logger.info(f"Video generated successfully: {video_id} ({duration_taken:.1f}s)")

                return {
                    "success": True,
                    "video_path": str(output_path),
                    "duration": duration_taken,
                }

            except Exception as e:
                error_msg = f"Exception during video generation: {str(e)}"
                logger.error(error_msg, exc_info=True)
                self._errors[video_id] = error_msg
                return {
                    "success": False,
                    "error": error_msg
                }


# Global generator instance
generator = VideoGenerator()
