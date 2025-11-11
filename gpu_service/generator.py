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
)

logger = logging.getLogger(__name__)


class VideoGenerator:
    """Wrapper for Open-Sora 2.0 video generation"""

    def __init__(self):
        self.opensora_path = Path(OPENSORA_PATH)
        self._generation_lock = asyncio.Lock()
        self._current_task: Optional[asyncio.Task] = None
        # Set conservative CUDA allocator defaults to reduce fragmentation
        os.environ.setdefault(
            "PYTORCH_CUDA_ALLOC_CONF",
            "expandable_segments:True,max_split_size_mb:128",
        )

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

    def is_processing(self) -> bool:
        """Return True while a torchrun task is still running."""
        task = self._current_task
        return task is not None and not task.done()

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
                # Calculate frames
                num_frames = self.calculate_frames(duration)
                logger.info(f"Generating {num_frames} frames for {duration}s video")

                # Create unique output directory for this job to avoid file conflicts
                job_output_dir = OUTPUT_DIR / video_id
                job_output_dir.mkdir(exist_ok=True)

                # Prepare output path
                output_path = OUTPUT_DIR / f"{video_id}.mp4"

                # Build command for STDiT v3
                cmd = [
                    "torchrun",
                    "--nproc_per_node", "1",
                    "--standalone",
                    "scripts/diffusion/inference.py",
                    MODEL_CONFIG_PATH,
                    "--ckpt", CHECKPOINT_PATH,  # STDiT v3 requires explicit checkpoint
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

                logger.info(f"Starting video generation: {video_id}")
                logger.debug(f"Command: {' '.join(cmd)}")

                start_time = time.time()

                # Run generation
                result = await self._run_generation(cmd)

                if result.returncode != 0:
                    err_text = (result.stderr or b"").decode(errors="ignore")
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
                            error_msg = (retry.stderr or b"").decode(errors="ignore") or err_text or "Unknown error"
                            logger.error(f"Generation failed after retry: {error_msg}")
                            return {"success": False, "error": error_msg}
                    else:
                        error_msg = err_text or "Unknown error"
                        logger.error(f"Generation failed: {error_msg}")
                        return {"success": False, "error": error_msg}

                # Find generated video file in job-specific directory
                generated_files = list(job_output_dir.glob("*.mp4"))
                if not generated_files:
                    logger.error("No video file generated")
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

                duration_taken = time.time() - start_time
                logger.info(f"Video generated successfully: {video_id} ({duration_taken:.1f}s)")

                return {
                    "success": True,
                    "video_path": str(output_path),
                    "duration": duration_taken,
                }

            except Exception as e:
                logger.error(f"Error generating video: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e)
                }


# Global generator instance
generator = VideoGenerator()
