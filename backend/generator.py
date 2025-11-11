"""
Open-Sora 2.0 Video Generator Wrapper
"""
import subprocess
import asyncio
import os
import re
import logging
from pathlib import Path
from typing import Optional, Dict
import json
import time

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
        self.jobs: Dict[str, Dict] = {}
        self._generation_lock = asyncio.Lock()
        self._current_task: Optional[asyncio.Task] = None

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

    def start_generation(
        self,
        *,
        video_id: str,
        image_path: str,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        motion_score: float,
        num_steps: int,
        guidance: float,
        guidance_img: float,
        seed: Optional[int],
        refine_prompt: bool
    ) -> bool:
        """
        Launch generation exactly once. Returns False if a job is already running.
        """
        if self.is_processing():
            return False

        self._current_task = asyncio.create_task(
            self.generate_video(
                video_id=video_id,
                image_path=image_path,
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                motion_score=motion_score,
                num_steps=num_steps,
                guidance=guidance,
                guidance_img=guidance_img,
                seed=seed,
                refine_prompt=refine_prompt,
            )
        )

        def _clear_task(_: asyncio.Task):
            self._current_task = None

        self._current_task.add_done_callback(_clear_task)
        return True

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

                # Create temporary config with custom parameters
                config_template_path = Path(self.opensora_path) / MODEL_CONFIG_PATH
                temp_config_path = job_output_dir / "config_temp.py"

                # Read base config and modify parameters
                with open(config_template_path, 'r') as f:
                    config_content = f.read()

                # Override sampling parameters
                config_content = re.sub(r'num_steps\s*=\s*[0-9]+', f'num_steps={num_steps}', config_content)
                config_content = re.sub(r'(?<!_)guidance\s*=\s*[0-9.]+', f'guidance={guidance}', config_content)
                config_content = re.sub(r'guidance_img\s*=\s*[0-9.]+', f'guidance_img={guidance_img}', config_content)

                # Write temporary config
                with open(temp_config_path, 'w') as f:
                    f.write(config_content)

                logger.info(f"Using temporary config with custom parameters")

                # Build command - use temporary config
                cmd = [
                    "torchrun",
                    "--nproc_per_node", "1",
                    "--standalone",
                    "scripts/diffusion/inference.py",
                    str(temp_config_path),
                    "--cond_type", "i2v_head",
                    "--ref", str(image_path),
                    "--prompt", enhanced_prompt,  # Use enhanced prompt
                    "--num_frames", str(num_frames),
                    "--aspect_ratio", aspect_ratio,
                    "--motion-score", str(motion_score),
                    "--save_dir", str(job_output_dir),
                    "--offload", "True",  # Memory optimization
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

                # Update job status
                self.jobs[video_id] = {
                    "status": "processing",
                    "start_time": time.time(),
                    "progress": 0,
                }

                logger.info(f"Starting video generation: {video_id}")
                logger.info(f"Working directory: {self.opensora_path}")
                logger.info(f"Command: {' '.join(cmd)}")

                # Run generation in subprocess
                # Use all available GPUs (don't restrict to GPU 0)
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=str(self.opensora_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                # Stream output
                stdout, stderr = await process.communicate()

                # Decode output with error handling
                stdout_text = stdout.decode(errors="replace") if stdout else ""
                stderr_text = stderr.decode(errors="replace") if stderr else ""

                if process.returncode != 0:
                    # Log full output on failure
                    if stdout_text:
                        logger.error(f"Generation stdout:\n{stdout_text}")
                    if stderr_text:
                        logger.error(f"Generation stderr:\n{stderr_text}")

                    error_msg = stderr_text or "Unknown error"
                    logger.error(f"Generation failed with returncode {process.returncode}: {error_msg}")
                    self.jobs[video_id]["status"] = "failed"
                    self.jobs[video_id]["error"] = error_msg
                    return {
                        "success": False,
                        "error": error_msg
                    }

                # Log output for successful runs
                if VERBOSE_GENERATION_LOGS:
                    # Full output when verbose logging is enabled
                    if stdout_text:
                        logger.info(f"Generation stdout (full):\n{stdout_text}")
                    if stderr_text:
                        logger.info(f"Generation stderr (full):\n{stderr_text}")
                else:
                    # Truncated output at debug level by default
                    if stdout_text:
                        logger.debug(f"Generation stdout (truncated): {stdout_text[-1000:]}")
                    if stderr_text:
                        logger.debug(f"Generation stderr (truncated): {stderr_text[-1000:]}")

                # Find generated video file in job-specific directory (search recursively)
                generated_files = list(job_output_dir.glob("**/*.mp4"))
                if not generated_files:
                    # Log directory contents for debugging
                    all_files = list(job_output_dir.glob("*"))
                    logger.error(f"No video file generated in {job_output_dir}")
                    logger.error(f"Directory contents: {[f.name for f in all_files]}")
                    logger.error(f"Last stdout: {stdout_text[-500:]}")
                    logger.error(f"Last stderr: {stderr_text[-500:]}")
                    self.jobs[video_id]["status"] = "failed"
                    return {
                        "success": False,
                        "error": "No video file generated"
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

                # Update job status
                duration_taken = time.time() - self.jobs[video_id]["start_time"]
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

            except Exception as e:
                logger.error(f"Error generating video: {e}", exc_info=True)
                self.jobs[video_id]["status"] = "failed"
                self.jobs[video_id]["error"] = str(e)
                return {
                    "success": False,
                    "error": str(e)
                }

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
