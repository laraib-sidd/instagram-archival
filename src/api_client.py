import time
import asyncio
import json
import getpass
import re
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
from instagram_private_api import Client, ClientError, ClientCheckpointRequiredError, ClientChallengeRequiredError
from .models import InstagramPost, MediaFile, Location, ArchiveConfig

class RateLimiter:
    def __init__(self, max_requests: int, time_window: float):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    async def acquire(self):
        now = time.time()
        # Remove old requests
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.time_window]
        
        if len(self.requests) >= self.max_requests:
            # Wait until we can make another request
            sleep_time = self.requests[0] + self.time_window - now
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            
        self.requests.append(now)

class InstagramAPIClient:
    def __init__(self):
        self.config = ArchiveConfig()
        self.api = None
        self.rate_limiter = RateLimiter(
            max_requests=self.config.max_requests_per_hour,
            time_window=3600  # 1 hour in seconds
        )

    async def authenticate(self):
        """Authenticate with Instagram"""
        try:
            self.api = Client(
                username=self.config.instagram_username,
                password=self.config.instagram_password
            )
            logger.info("Successfully authenticated with Instagram")
        except (ClientCheckpointRequiredError, ClientChallengeRequiredError) as e:
            logger.info("Security verification required.")
            
            if isinstance(e, ClientCheckpointRequiredError):
                # Handle email/phone verification code
                logger.info("Please check your email/phone for verification code.")
                verification_code = input("Enter the verification code sent to your email/phone: ").strip()
                verification_method = 'code'
            else:
                # Handle mobile app verification
                logger.info("Please check your Instagram mobile app for verification prompt.")
                logger.info("1. Open Instagram app on your phone")
                logger.info("2. Tap the notification or go to Settings -> Security")
                logger.info("3. Approve the login request")
                input("Press Enter after approving the login request in your Instagram app...")
                verification_method = 'challenge'
            
            try:
                # Create a new client instance with verification
                self.api = Client(
                    username=self.config.instagram_username,
                    password=self.config.instagram_password,
                    verification_code=verification_code if verification_method == 'code' else None,
                    challenge_response=True if verification_method == 'challenge' else None
                )
                logger.info("Successfully authenticated with verification")
            except ClientError as e:
                logger.error(f"Failed to verify: {str(e)}")
                raise
        except ClientError as e:
            logger.error(f"Failed to authenticate with Instagram: {str(e)}")
            raise

    def _shortcode_to_media_id(self, shortcode: str) -> str:
        """Convert an Instagram shortcode to a media ID
        Args:
            shortcode: The shortcode from the Instagram URL
        Returns:
            The numeric media ID
        """
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
        media_id = 0
        for char in shortcode:
            media_id = media_id * 64 + alphabet.index(char)
        return str(media_id)

    async def archive_post(self, post_id: str) -> bool:
        """Archive a post using the Instagram Private API
        Args:
            post_id: The ID or shortcode of the post
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            await self.rate_limiter.acquire()
            
            # Convert shortcode to media ID if needed
            if not post_id.isdigit():
                post_id = self._shortcode_to_media_id(post_id)
            
            # Use the private API to archive the post
            result = self.api.media_archive(post_id)
            
            # Check if the archive was successful
            if result.get('status') == 'ok':
                logger.info(f"Successfully archived post {post_id}")
                return True
            else:
                logger.error(f"Failed to archive post {post_id}: {result}")
                return False

        except ClientError as e:
            logger.error(f"Error archiving post {post_id}: {str(e)}")
            return False

    async def fetch_single_post(self, post_id: str) -> Optional[InstagramPost]:
        """Fetch metadata for a single post
        Args:
            post_id: The ID or shortcode of the post
        Returns:
            InstagramPost object if successful, None otherwise
        """
        try:
            await self.rate_limiter.acquire()
            
            # Convert shortcode to media ID if needed
            if not post_id.isdigit():
                post_id = self._shortcode_to_media_id(post_id)
                logger.info(f"Converted shortcode to media ID: {post_id}")
            
            # Fetch post info
            post_info = self.api.media_info(post_id)
            if not post_info or 'items' not in post_info or not post_info['items']:
                logger.error(f"Could not fetch info for post {post_id}")
                return None

            # Convert to InstagramPost model
            post = await self._convert_to_post_model(post_info['items'][0])
            logger.info(f"Successfully fetched post {post_id}")
            return post

        except ClientError as e:
            logger.error(f"Error fetching post {post_id}: {str(e)}")
            return None

    async def fetch_all_posts(self) -> List[InstagramPost]:
        """Fetch all posts from the authenticated user's account"""
        posts = []
        try:
            user_feed = self.api.self_feed()
            while True:
                await self.rate_limiter.acquire()
                
                for item in user_feed['items']:
                    post = await self._convert_to_post_model(item)
                    posts.append(post)
                
                if not user_feed.get('more_available'):
                    break
                    
                user_feed = self.api.self_feed(max_id=user_feed['next_max_id'])
                
        except ClientError as e:
            logger.error(f"Error fetching posts: {str(e)}")
            raise
            
        return posts

    async def _convert_to_post_model(self, item: Dict) -> InstagramPost:
        """Convert API response to InstagramPost model"""
        media_files = []
        
        # Handle carousel albums
        if item['media_type'] == 8:  # Carousel
            for carousel_item in item['carousel_media']:
                media_files.append(self._extract_media_file(carousel_item))
        else:
            media_files.append(self._extract_media_file(item))

        # Extract hashtags from caption
        hashtags = []
        if item.get('caption') and item['caption'].get('text'):
            hashtags = [word[1:] for word in item['caption']['text'].split() 
                       if word.startswith('#')]

        # Create location if available
        location = None
        if item.get('location'):
            location = Location(
                id=item['location'].get('pk'),
                name=item['location'].get('name'),
                latitude=item['location'].get('lat'),
                longitude=item['location'].get('lng')
            )

        return InstagramPost(
            id=item['id'],
            caption=item.get('caption', {}).get('text'),
            media_type='CAROUSEL_ALBUM' if item['media_type'] == 8 else 
                      'VIDEO' if item['media_type'] == 2 else 'IMAGE',
            media_files=media_files,
            timestamp=datetime.fromtimestamp(item['taken_at']),
            permalink=f"https://www.instagram.com/p/{item['code']}/",
            likes_count=item.get('like_count'),
            comments_count=item.get('comment_count'),
            hashtags=hashtags,
            location=location
        )

    def _extract_media_file(self, item: Dict) -> MediaFile:
        """Extract media file information from API response"""
        if item['media_type'] == 2:  # Video
            url = item['video_versions'][0]['url']
            width = item['video_versions'][0]['width']
            height = item['video_versions'][0]['height']
            media_type = 'video'
        else:  # Image
            url = item['image_versions2']['candidates'][0]['url']
            width = item['image_versions2']['candidates'][0]['width']
            height = item['image_versions2']['candidates'][0]['height']
            media_type = 'image'

        return MediaFile(
            url=url,
            type=media_type,
            width=width,
            height=height
        )

    async def cleanup(self):
        """Cleanup resources"""
        # No cleanup needed for now, but keeping the method for future use
        pass 