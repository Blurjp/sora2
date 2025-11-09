"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class AspectRatio(str, Enum):
    """Supported aspect ratios"""
    RATIO_16_9 = "16:9"
    RATIO_9_16 = "9:16"
    RATIO_1_1 = "1:1"
    RATIO_2_39_1 = "2.39:1"


class VideoStatus(str, Enum):
    """Video generation status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerateRequest(BaseModel):
    """Video generation request"""
    prompt: str = Field(..., min_length=1, max_length=1000, description="Text prompt for video generation")
    duration: int = Field(15, ge=10, le=20, description="Video duration in seconds")
    aspect_ratio: AspectRatio = Field(AspectRatio.RATIO_16_9, description="Video aspect ratio")
    motion_score: float = Field(0.5, ge=0.0, le=1.0, description="Motion intensity (0.0-1.0)")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    refine_prompt: bool = Field(False, description="Use AI to refine the prompt")


class GenerateResponse(BaseModel):
    """Video generation response"""
    video_id: str = Field(..., description="Unique video identifier")
    status: VideoStatus = Field(..., description="Generation status")
    message: str = Field(..., description="Status message")


class StatusResponse(BaseModel):
    """Video status response"""
    video_id: str
    status: VideoStatus
    progress: Optional[float] = Field(None, ge=0.0, le=100.0, description="Progress percentage")
    video_url: Optional[str] = Field(None, description="Download URL when completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    estimated_time: Optional[int] = Field(None, description="Estimated completion time in seconds")


class VideoInfo(BaseModel):
    """Video metadata"""
    video_id: str
    prompt: str
    duration: int
    aspect_ratio: str
    created_at: str
    file_size: Optional[int] = None
    file_path: Optional[str] = None
