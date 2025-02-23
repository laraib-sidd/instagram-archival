from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from pathlib import Path
import os
from dotenv import load_dotenv

class Location(BaseModel):
    id: Optional[str]
    name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]

class MediaFile(BaseModel):
    url: str
    type: str  # 'image', 'video', 'carousel_item'
    width: Optional[int]
    height: Optional[int]

class InstagramPost(BaseModel):
    id: str
    caption: Optional[str]
    media_type: str  # 'IMAGE', 'VIDEO', 'CAROUSEL_ALBUM'
    media_files: List[MediaFile]
    timestamp: datetime
    permalink: str
    likes_count: Optional[int]
    comments_count: Optional[int]
    hashtags: List[str] = Field(default_factory=list)
    location: Optional[Location]
    is_archived: bool = False
    local_path: Optional[Path] = None

class ArchiveConfig(BaseModel):
    """Configuration settings loaded from environment variables"""
    def __init__(self, **data):
        load_dotenv()
        super().__init__(**data)

    # Instagram API settings
    instagram_username: str = Field(default_factory=lambda: os.getenv('INSTAGRAM_USERNAME'))
    instagram_password: str = Field(default_factory=lambda: os.getenv('INSTAGRAM_PASSWORD'))
    instagram_app_id: str = Field(default_factory=lambda: os.getenv('INSTAGRAM_APP_ID'))
    instagram_app_secret: str = Field(default_factory=lambda: os.getenv('INSTAGRAM_APP_SECRET'))

    # Storage settings
    archive_base_path: Path = Field(
        default_factory=lambda: Path(os.getenv('ARCHIVE_BASE_PATH', './Instagram_Archive'))
    )
    store_locally: bool = Field(
        default_factory=lambda: os.getenv('STORE_LOCALLY', 'true').lower() == 'true'
    )

    # Automation settings
    automation_interval_hours: int = Field(
        default_factory=lambda: int(os.getenv('AUTOMATION_INTERVAL_HOURS', '24'))
    )
    max_retries: int = Field(
        default_factory=lambda: int(os.getenv('MAX_RETRIES', '3'))
    )
    request_timeout: int = Field(
        default_factory=lambda: int(os.getenv('REQUEST_TIMEOUT', '30'))
    )

    # Rate limiting
    max_requests_per_hour: int = Field(
        default_factory=lambda: int(os.getenv('MAX_REQUESTS_PER_HOUR', '200'))
    )
    delay_between_requests: float = Field(
        default_factory=lambda: float(os.getenv('DELAY_BETWEEN_REQUESTS', '2'))
    ) 