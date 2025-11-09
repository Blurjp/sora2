"""
Open-Sora 2.0 Video Generator Wrapper
"""
import subprocess
import asyncio
import os
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
)

logger = logging.getLogger(__name__)


class VideoGenerator:
    """Wrapper for Open-Sora 2.0 video generation"""

    def __init__(self):
        self.opensora_path = Path(OPENSORA_PATH)
        self.jobs: Dict[str, Dict] = {}

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

    async def generate_video(
        self,
        video_id: str,
        image_path: str,
        prompt: str,
        duration: int = 15,
        aspect_ratio: str = "16:9",
        motion_score: float = 0.5,
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
        try:
            # Calculate frames
            num_frames = self.calculate_frames(duration)
            logger.info(f"Generating {num_frames} frames for {duration}s video")

            # Create unique output directory for this job to avoid file conflicts
            job_output_dir = OUTPUT_DIR / video_id
            job_output_dir.mkdir(exist_ok=True)

            # Prepare output path
            output_path = OUTPUT_DIR / f"{video_id}.mp4"

            # Build command
            cmd = [
                "torchrun",
                "--nproc_per_node", "1",
                "--standalone",
                "scripts/diffusion/inference.py",
                MODEL_CONFIG_PATH,
                "--cond_type", "i2v_head",
                "--ref", str(image_path),
                "--prompt", prompt,
                "--num_frames", str(num_frames),
                "--aspect_ratio", aspect_ratio,
                "--motion-score", str(motion_score),
                "--save_dir", str(job_output_dir),
                "--offload", "True",  # Memory optimization
            ]

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
            logger.debug(f"Command: {' '.join(cmd)}")

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

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Generation failed: {error_msg}")
                self.jobs[video_id]["status"] = "failed"
                self.jobs[video_id]["error"] = error_msg
                return {
                    "success": False,
                    "error": error_msg
                }

            # Find generated video file in job-specific directory
            generated_files = list(job_output_dir.glob("*.mp4"))
            if not generated_files:
                logger.error("No video file generated")
                self.jobs[video_id]["status"] = "failed"
                return {
                    "success": False,
                    "error": "No video file generated"
                }

            # Get the generated file (should only be one in this directory)
            generated_file = generated_files[0]

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
