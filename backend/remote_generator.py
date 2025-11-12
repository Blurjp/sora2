"""
Remote Video Generator - Proxies requests to GPU service
"""
import asyncio
import logging
from typing import Optional, Dict
from pathlib import Path

from .gpu_client import GPUClient
from .config import GPU_SERVICE_URL, GPU_API_KEY, OUTPUT_DIR

logger = logging.getLogger(__name__)


class RemoteVideoGenerator:
    """Wrapper that sends generation requests to remote GPU service"""

    def __init__(self, gpu_url: str = GPU_SERVICE_URL, api_key: Optional[str] = GPU_API_KEY):
        self.gpu_client = GPUClient(gpu_url, api_key)
        self.jobs: Dict[str, Dict] = {}
        self._current_video_id: Optional[str] = None

    async def health_check(self) -> Dict:
        """Check if GPU service is available"""
        return await self.gpu_client.health_check()

    def is_processing(self) -> bool:
        """Check if a generation is currently in progress"""
        return self._current_video_id is not None

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
        """
        Start video generation on remote GPU.
        Returns False if already processing.
        """
        if self.is_processing():
            return False

        # Mark as processing
        self._current_video_id = video_id

        # Create background task
        asyncio.create_task(
            self._generate_and_download(
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
                face_detail=face_detail,
                aesthetic_score=aesthetic_score,
                sharpness=sharpness,
                negative_prompt=negative_prompt,
                face_enhance=face_enhance,
                denoise=denoise,
                temporal_smoothing=temporal_smoothing,
                seed=seed,
                refine_prompt=refine_prompt
            )
        )

        return True

    async def _generate_and_download(
        self,
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
        face_detail: float,
        aesthetic_score: float,
        sharpness: float,
        negative_prompt: Optional[str],
        face_enhance: bool,
        denoise: bool,
        temporal_smoothing: bool,
        seed: Optional[int],
        refine_prompt: bool
    ):
        """
        Internal method to generate video and download result
        """
        try:
            # Update job status
            self.jobs[video_id] = {
                "status": "processing",
                "progress": 0,
                "message": "Sending request to GPU service..."
            }

            # Send generation request to GPU service
            logger.info(f"Sending {mode.upper()} generation request to GPU service: {video_id}")
            result = await self.gpu_client.generate_video(
                mode=mode,
                image_path=image_path,
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
                refine_prompt=refine_prompt
            )

            if "error" in result:
                logger.error(f"GPU service error: {result['error']}")
                self.jobs[video_id] = {
                    "status": "failed",
                    "error": result["error"]
                }
                return

            # Get the remote video_id from GPU service
            remote_video_id = result.get("video_id")
            if not remote_video_id:
                logger.error("No video_id returned from GPU service")
                self.jobs[video_id] = {
                    "status": "failed",
                    "error": "Invalid response from GPU service"
                }
                return

            logger.info(f"Remote generation started: {remote_video_id}")

            # Update status
            self.jobs[video_id]["message"] = "Video is being generated on GPU..."
            self.jobs[video_id]["progress"] = 10

            # Poll for completion
            max_polls = 300  # 5 minutes with 1 second intervals
            for i in range(max_polls):
                await asyncio.sleep(1)

                # Check status on GPU service
                status = await self.gpu_client.check_status(remote_video_id)

                if status.get("status") == "completed":
                    logger.info(f"Remote generation completed: {remote_video_id}")

                    # Download the video
                    self.jobs[video_id]["message"] = "Downloading video..."
                    self.jobs[video_id]["progress"] = 90

                    output_path = OUTPUT_DIR / f"{video_id}.mp4"
                    success = await self.gpu_client.download_video(
                        remote_video_id,
                        str(output_path)
                    )

                    if success:
                        # Delete from GPU service to save space
                        await self.gpu_client.delete_video(remote_video_id)

                        self.jobs[video_id] = {
                            "status": "completed",
                            "progress": 100,
                            "output_path": str(output_path)
                        }
                        logger.info(f"Video generation completed: {video_id}")
                    else:
                        self.jobs[video_id] = {
                            "status": "failed",
                            "error": "Failed to download video from GPU service"
                        }
                    break

                elif status.get("status") == "failed":
                    error = status.get("error", "Unknown error")
                    logger.error(f"Remote generation failed: {error}")
                    self.jobs[video_id] = {
                        "status": "failed",
                        "error": error
                    }
                    break

                elif status.get("status") == "not_found":
                    logger.error(f"Video not found on GPU service: {remote_video_id}")
                    self.jobs[video_id] = {
                        "status": "failed",
                        "error": "Video not found on GPU service"
                    }
                    break

                else:
                    # Still processing, update progress
                    progress = min(10 + (i * 80 // max_polls), 85)
                    self.jobs[video_id]["progress"] = progress

            else:
                # Timeout
                logger.error(f"Generation timeout: {video_id}")
                self.jobs[video_id] = {
                    "status": "failed",
                    "error": "Generation timeout (5 minutes exceeded)"
                }

        except Exception as e:
            logger.error(f"Error in remote generation: {e}", exc_info=True)
            self.jobs[video_id] = {
                "status": "failed",
                "error": str(e)
            }

        finally:
            # Clear current video ID
            self._current_video_id = None

    def get_job_status(self, video_id: str) -> Optional[Dict]:
        """Get status of a generation job"""
        return self.jobs.get(video_id)

    async def cleanup(self):
        """Clean up resources"""
        await self.gpu_client.close()


# Global remote generator instance
remote_generator = RemoteVideoGenerator()
