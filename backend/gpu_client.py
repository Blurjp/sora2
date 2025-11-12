"""
GPU Client - Communicates with remote GPU service
"""
import logging
import aiohttp
import asyncio
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class GPUClient:
    """Client for communicating with remote GPU service"""

    def __init__(self, gpu_url: str, api_key: Optional[str] = None):
        """
        Initialize GPU client

        Args:
            gpu_url: Base URL of GPU service (e.g., "http://lambda-instance:8001")
            api_key: Optional API key for authentication
        """
        self.gpu_url = gpu_url.rstrip('/')
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            headers = {}
            if self.api_key:
                headers['X-API-Key'] = self.api_key

            timeout = aiohttp.ClientTimeout(total=600)  # 10 minute timeout for generation
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        return self._session

    async def close(self):
        """Close the client session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def health_check(self) -> Dict:
        """
        Check if GPU service is healthy and available

        Returns:
            Dictionary with health status
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.gpu_url}/api/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"GPU service health: {data}")
                    return data
                else:
                    error = await response.text()
                    logger.error(f"GPU health check failed: {error}")
                    return {"status": "unhealthy", "error": error}
        except Exception as e:
            logger.error(f"GPU health check error: {e}")
            return {"status": "error", "error": str(e)}

    async def generate_video(
        self,
        mode: str,
        image_path: Optional[str],
        prompt: str,
        duration: int = 15,
        aspect_ratio: str = "16:9",
        motion_score: float = 0.5,
        num_steps: int = 120,
        guidance: float = 12.0,
        guidance_img: float = 3.5,
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
        Send video generation request to GPU service

        Args:
            mode: Generation mode (i2v or t2v)
            image_path: Path to input image file (required for i2v)
            prompt: Text prompt for generation
            duration: Video duration in seconds
            aspect_ratio: Video aspect ratio
            motion_score: Motion intensity
            num_steps: Diffusion steps
            guidance: Text guidance strength
            guidance_img: Image guidance strength
            face_detail: Face detail level
            aesthetic_score: Aesthetic quality
            sharpness: Sharpness level
            negative_prompt: What to avoid
            face_enhance: Enable face enhancement
            denoise: Enable denoising
            temporal_smoothing: Enable temporal smoothing
            seed: Random seed
            refine_prompt: Whether to refine prompt

        Returns:
            Dictionary with video_id and status
        """
        try:
            session = await self._get_session()

            # Prepare form data
            data = aiohttp.FormData()

            # Add generation mode
            data.add_field('mode', mode)

            # Add image file for i2v mode only
            if mode == 'i2v' and image_path:
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                data.add_field('image',
                              image_data,
                              filename=Path(image_path).name,
                              content_type='application/octet-stream')

            # Add form fields
            data.add_field('prompt', prompt)
            data.add_field('duration', str(duration))
            data.add_field('aspect_ratio', aspect_ratio)
            data.add_field('motion_score', str(motion_score))
            data.add_field('num_steps', str(num_steps))
            data.add_field('guidance', str(guidance))
            data.add_field('guidance_img', str(guidance_img))
            data.add_field('face_detail', str(face_detail))
            data.add_field('aesthetic_score', str(aesthetic_score))
            data.add_field('sharpness', str(sharpness))
            if negative_prompt:
                data.add_field('negative_prompt', negative_prompt)
            data.add_field('face_enhance', str(face_enhance).lower())
            data.add_field('denoise', str(denoise).lower())
            data.add_field('temporal_smoothing', str(temporal_smoothing).lower())
            if seed is not None:
                data.add_field('seed', str(seed))
            data.add_field('refine_prompt', str(refine_prompt).lower())

            # Send request
            async with session.post(f"{self.gpu_url}/api/generate", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"GPU generation started: {result}")
                    return result
                elif response.status == 429:
                    error_data = await response.json()
                    return {
                        "error": error_data.get("detail", "GPU busy"),
                        "status": "busy"
                    }
                else:
                    error = await response.text()
                    logger.error(f"GPU generation failed: {error}")
                    return {"error": error, "status": "failed"}

        except Exception as e:
            logger.error(f"Error sending generation request: {e}", exc_info=True)
            return {"error": str(e), "status": "error"}

    async def check_status(self, video_id: str) -> Dict:
        """
        Check status of video generation

        Args:
            video_id: Video ID to check

        Returns:
            Dictionary with status information
        """
        try:
            session = await self._get_session()

            async with session.get(f"{self.gpu_url}/api/status/{video_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Status check failed: {error}")
                    return {"status": "error", "error": error}

        except Exception as e:
            logger.error(f"Error checking status: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def download_video(self, video_id: str, output_path: str) -> bool:
        """
        Download generated video from GPU service

        Args:
            video_id: Video ID to download
            output_path: Local path to save video

        Returns:
            True if successful, False otherwise
        """
        try:
            session = await self._get_session()

            async with session.get(f"{self.gpu_url}/api/download/{video_id}") as response:
                if response.status == 200:
                    # Write video to file
                    with open(output_path, 'wb') as f:
                        while True:
                            chunk = await response.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)

                    logger.info(f"Video downloaded: {output_path}")
                    return True
                else:
                    error = await response.text()
                    logger.error(f"Video download failed: {error}")
                    return False

        except Exception as e:
            logger.error(f"Error downloading video: {e}", exc_info=True)
            return False

    async def delete_video(self, video_id: str) -> bool:
        """
        Delete video from GPU service

        Args:
            video_id: Video ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            session = await self._get_session()

            async with session.delete(f"{self.gpu_url}/api/video/{video_id}") as response:
                if response.status == 200:
                    logger.info(f"Video deleted from GPU: {video_id}")
                    return True
                else:
                    error = await response.text()
                    logger.warning(f"Failed to delete video: {error}")
                    return False

        except Exception as e:
            logger.error(f"Error deleting video: {e}", exc_info=True)
            return False
