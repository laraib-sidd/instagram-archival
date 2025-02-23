import os
import json
import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
from dotenv import load_dotenv
from instagram_private_api import Client, ClientError

from .models import InstagramPost, ArchiveConfig
from .storage import LocalStorage
from .api_client import InstagramAPIClient

class InstagramArchiver:
    def __init__(self):
        load_dotenv()
        self.config = ArchiveConfig()
        self.api_client = InstagramAPIClient()
        self.storage = LocalStorage(base_path=self.config.archive_base_path)
        
        # Setup logging
        logger.add(
            "logs/instagram_archiver_{time}.log",
            rotation="1 day",
            retention="1 month",
            level="INFO"
        )

    async def initialize(self):
        """Initialize connections and authenticate"""
        await self.api_client.authenticate()

    async def archive_all_posts(self):
        """Main method to archive all posts"""
        try:
            # Fetch all posts metadata
            posts = await self.api_client.fetch_all_posts()
            logger.info(f"Found {len(posts)} posts to archive")

            # Archive posts on Instagram
            await self.archive_posts_on_instagram(posts)

            # Download media files
            await self.download_media_files(posts)

            # Save metadata
            self.save_metadata(posts)

            logger.info("Archival process completed successfully")
            
        except Exception as e:
            logger.error(f"Error during archival process: {str(e)}")
            raise

    async def test_single_post(self, post_url: str):
        """Test archival process with a single post
        Args:
            post_url: Instagram post URL or shortcode
                     (e.g., https://www.instagram.com/p/ABC123 or just ABC123)
        """
        try:
            # Extract post ID from URL
            if 'instagram.com' in post_url:
                post_id = re.search(r'instagram\.com/p/([^/]+)', post_url).group(1)
            else:
                post_id = post_url.strip()

            logger.info(f"Testing archival process with post ID: {post_id}")

            # Fetch single post metadata
            post = await self.api_client.fetch_single_post(post_id)
            if not post:
                raise ValueError(f"Could not fetch post with ID: {post_id}")

            # Archive post on Instagram
            logger.info("Attempting to archive post on Instagram...")
            await self.api_client.archive_post(post_id)

            # Download media files
            logger.info("Downloading media files...")
            await self.storage.save_media(post)

            # Save metadata
            logger.info("Saving metadata...")
            self.storage.save_metadata([post])

            logger.info("Test archival process completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error during test archival process: {str(e)}")
            raise

    async def archive_posts_on_instagram(self, posts: List[InstagramPost]):
        """Archive posts on Instagram using API"""
        logger.info("Starting to archive posts on Instagram")
        for post in posts:
            try:
                await self.api_client.archive_post(post.id)
                logger.info(f"Successfully archived post {post.id} on Instagram")
            except Exception as e:
                logger.error(f"Failed to archive post {post.id}: {str(e)}")

    async def download_media_files(self, posts: List[InstagramPost]):
        """Download media files locally"""
        logger.info("Starting media downloads")
        for post in posts:
            try:
                await self.storage.save_media(post)
                logger.info(f"Successfully downloaded media for post {post.id}")
            except Exception as e:
                logger.error(f"Failed to download media for post {post.id}: {str(e)}")

    def save_metadata(self, posts: List[InstagramPost]):
        """Save posts metadata in both JSON and CSV formats"""
        self.storage.save_metadata(posts)
        logger.info("Successfully saved metadata")

    async def cleanup(self):
        """Cleanup resources"""
        await self.api_client.cleanup()

    @classmethod
    async def run(cls, test_post_url: Optional[str] = None):
        """Main entry point to run the archiver
        Args:
            test_post_url: Optional URL or ID of a single post to test with
        """
        archiver = cls()
        try:
            await archiver.initialize()
            if test_post_url:
                await archiver.test_single_post(test_post_url)
            else:
                await archiver.archive_all_posts()
        finally:
            await archiver.cleanup()

if __name__ == "__main__":
    import sys
    test_post = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(InstagramArchiver.run(test_post)) 