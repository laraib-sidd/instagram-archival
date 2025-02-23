import os
import json
import aiohttp
import pandas as pd
from pathlib import Path
from typing import List
from loguru import logger
from datetime import datetime
from .models import InstagramPost

class LocalStorage:
    def __init__(self, base_path: str = './Instagram_Archive'):
        self.base_path = Path(base_path)
        self._setup_directories()

    def _setup_directories(self):
        """Create necessary directories if they don't exist"""
        for dir_name in ['images', 'videos', 'metadata']:
            (self.base_path / dir_name).mkdir(parents=True, exist_ok=True)

    async def save_media(self, post: InstagramPost):
        """Download and save media files from a post"""
        try:
            async with aiohttp.ClientSession() as session:
                for media_file in post.media_files:
                    # Determine file extension from URL
                    ext = '.mp4' if media_file.type == 'video' else '.jpg'
                    
                    # Create filename with timestamp and post ID
                    timestamp = post.timestamp.strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{post.id}{ext}"
                    
                    # Determine directory based on media type
                    directory = 'videos' if media_file.type == 'video' else 'images'
                    filepath = self.base_path / directory / filename

                    # Download file
                    async with session.get(media_file.url) as response:
                        if response.status == 200:
                            with open(filepath, 'wb') as f:
                                f.write(await response.read())
                            logger.info(f"Successfully saved media file: {filename}")
                        else:
                            logger.error(f"Failed to download media file: {filename}")
                            raise Exception(f"HTTP {response.status}: Failed to download media")

                    # Update post's local path
                    post.local_path = filepath

        except Exception as e:
            logger.error(f"Error saving media for post {post.id}: {str(e)}")
            raise

    def save_metadata(self, posts: List[InstagramPost]):
        """Save posts metadata in both JSON and CSV formats"""
        try:
            # Convert posts to dictionary format
            posts_data = [self._post_to_dict(post) for post in posts]
            
            # Save as JSON
            json_path = self.base_path / 'metadata' / 'posts_metadata.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(posts_data, f, indent=2, default=str)
            logger.info(f"Saved JSON metadata to {json_path}")

            # Save as CSV
            csv_path = self.base_path / 'metadata' / 'posts_metadata.csv'
            df = pd.DataFrame(posts_data)
            df.to_csv(csv_path, index=False)
            logger.info(f"Saved CSV metadata to {csv_path}")

        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
            raise

    def _post_to_dict(self, post: InstagramPost) -> dict:
        """Convert InstagramPost to a dictionary format suitable for storage"""
        return {
            'id': post.id,
            'caption': post.caption,
            'media_type': post.media_type,
            'timestamp': post.timestamp.isoformat(),
            'permalink': post.permalink,
            'likes_count': post.likes_count,
            'comments_count': post.comments_count,
            'hashtags': ','.join(post.hashtags),
            'location_name': post.location.name if post.location else None,
            'location_lat': post.location.latitude if post.location else None,
            'location_lng': post.location.longitude if post.location else None,
            'is_archived': post.is_archived,
            'local_path': str(post.local_path) if post.local_path else None,
            'media_count': len(post.media_files),
            'download_date': datetime.now().isoformat()
        } 