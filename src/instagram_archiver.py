import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
from dotenv import load_dotenv
from instagram_private_api import Client, ClientError

from .models import InstagramPost, ArchiveConfig
from .browser_automation import InstagramBrowserAutomation
from .storage import LocalStorage
from .api_client import InstagramAPIClient

class InstagramArchiver:
    def __init__(self):
        load_dotenv()
        self.config = ArchiveConfig()
        self.api_client = InstagramAPIClient()
        self.storage = LocalStorage(base_path=self.config.archive_base_path)
        self.browser_automation = InstagramBrowserAutomation()
        
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
        await self.browser_automation.initialize()

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

    async def archive_posts_on_instagram(self, posts: List[InstagramPost]):
        """Archive posts on Instagram using browser automation"""
        logger.info("Starting to archive posts on Instagram")
        for post in posts:
            try:
                await self.browser_automation.archive_post(post.id)
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
        await self.browser_automation.cleanup()
        await self.api_client.cleanup()

    @classmethod
    async def run(cls):
        """Main entry point to run the archiver"""
        archiver = cls()
        try:
            await archiver.initialize()
            await archiver.archive_all_posts()
        finally:
            await archiver.cleanup()

if __name__ == "__main__":
    asyncio.run(InstagramArchiver.run()) 