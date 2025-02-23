import asyncio
from playwright.async_api import async_playwright, Browser, Page
from loguru import logger
from .models import ArchiveConfig

class InstagramBrowserAutomation:
    def __init__(self):
        self.config = ArchiveConfig()
        self.browser = None
        self.context = None
        self.page = None

    async def initialize(self):
        """Initialize the browser and log in to Instagram"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

            # Login to Instagram
            await self._login()
            logger.info("Successfully initialized browser automation")
        except Exception as e:
            logger.error(f"Failed to initialize browser automation: {str(e)}")
            await self.cleanup()
            raise

    async def _login(self):
        """Log in to Instagram"""
        try:
            await self.page.goto('https://www.instagram.com/accounts/login/')
            await asyncio.sleep(2)  # Wait for page to load

            # Handle cookie consent if present
            try:
                await self.page.click('button[text="Allow essential and optional cookies"]')
                await asyncio.sleep(1)
            except:
                pass  # Cookie consent might not appear

            # Enter credentials
            await self.page.fill('input[name="username"]', self.config.instagram_username)
            await self.page.fill('input[name="password"]', self.config.instagram_password)
            
            # Click login button
            await self.page.click('button[type="submit"]')
            
            # Wait for login to complete
            await self.page.wait_for_navigation()
            
            # Handle "Save Login Info" popup if it appears
            try:
                await self.page.click('button:has-text("Not Now")')
            except:
                pass

            # Handle notifications popup if it appears
            try:
                await self.page.click('button:has-text("Not Now")')
            except:
                pass

            logger.info("Successfully logged in to Instagram")
        except Exception as e:
            logger.error(f"Failed to log in to Instagram: {str(e)}")
            raise

    async def archive_post(self, post_id: str):
        """Archive a single post"""
        try:
            # Navigate to post
            await self.page.goto(f'https://www.instagram.com/p/{post_id}/')
            await asyncio.sleep(2)  # Wait for page to load

            # Click more options button (three dots)
            await self.page.click('button[aria-label="More options"]')
            await asyncio.sleep(1)

            # Click archive option
            await self.page.click('button:has-text("Archive")')
            await asyncio.sleep(1)

            # Verify archive action
            try:
                await self.page.wait_for_selector('text=Post archived', timeout=5000)
                logger.info(f"Successfully archived post {post_id}")
            except:
                logger.warning(f"Could not verify if post {post_id} was archived")

        except Exception as e:
            logger.error(f"Failed to archive post {post_id}: {str(e)}")
            raise

    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("Successfully cleaned up browser automation resources")
        except Exception as e:
            logger.error(f"Error during browser cleanup: {str(e)}")
            raise 