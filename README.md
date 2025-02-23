# Instagram Post Archiver

A robust Python tool for automatically archiving Instagram posts both on Instagram itself and locally. This tool handles all types of Instagram posts (images, videos, reels, carousels) and stores them with their associated metadata.

## Features

- Archives posts on Instagram using browser automation
- Downloads all media files in their highest available resolution
- Stores comprehensive metadata in both JSON and CSV formats
- Handles rate limiting and API restrictions
- Provides detailed logging and error handling
- Supports all media types (images, videos, reels, carousels)
- Test mode for single post archival

## Prerequisites

- Python 3.8 or higher
- Instagram account credentials
- Instagram Developer App credentials (for API access)

## Getting Instagram Credentials

### 1. Instagram Account Credentials
These are your regular Instagram login credentials:
- `INSTAGRAM_USERNAME`: Your Instagram username
- `INSTAGRAM_PASSWORD`: Your Instagram password

### 2. Instagram Developer Credentials
To get your Instagram Developer credentials (APP_ID and APP_SECRET):

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Log in with your Facebook account (must be linked to your Instagram account)
3. Create a New App:
   - Click "Create App"
   - At "Add use cases" screen, scroll down and select "Other"
   - Choose "Business" as the app type
   - Fill in your app name and contact email
   - Click "Create App"

4. Add Instagram Permissions:
   - In your app dashboard, click "Add Products"
   - Find and add these products:
     * Instagram Graph API
     * Instagram Basic Display API
   - Follow the setup wizard for each

5. Configure Your App:
   - Go to "Instagram Basic Display" → "Basic Display"
   - Under "OAuth Redirect URLs" add:
     ```
     http://localhost:8000/auth/
     ```
   - Add your app's privacy policy URL (can be your GitHub repo URL)
   - Under "App Review", request these permissions:
     * instagram_graph_user_profile
     * instagram_graph_user_media
     * instagram_basic_display

6. Get Your Credentials:
   - `INSTAGRAM_APP_ID`: Find this in your app's basic settings
   - `INSTAGRAM_APP_SECRET`: In basic settings, click "Show" next to "App Secret"

### 3. Additional Setup
1. Link Your Instagram Account:
   - In your app's Instagram Basic Display settings
   - Click "Add or Remove Instagram Testers"
   - Add your Instagram account as a tester
   - Open Instagram and accept the tester invitation

2. Generate Access Token:
   - In Instagram Basic Display settings
   - Click "Generate Token"
   - Follow the authentication flow
   - Save the token securely

### Security Notes:
- Never share your credentials or commit them to version control
- Use environment variables or secure credential storage
- Regularly rotate your app secret
- Monitor your app's usage in Meta for Developers dashboard

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/instagram-archiver.git
cd instagram-archiver
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials and settings:
```env
# Instagram API Credentials
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
INSTAGRAM_APP_ID=your_app_id
INSTAGRAM_APP_SECRET=your_app_secret

# Storage Configuration
ARCHIVE_BASE_PATH=./Instagram_Archive

# Automation Settings
AUTOMATION_INTERVAL_HOURS=24
MAX_RETRIES=3
REQUEST_TIMEOUT=30

# Rate Limiting
MAX_REQUESTS_PER_HOUR=200
DELAY_BETWEEN_REQUESTS=2
```

## Usage

### Archive All Posts

Run the archiver to process all posts:
```bash
python -m src.instagram_archiver
```

The tool will:
1. Authenticate with Instagram
2. Fetch all posts from your account
3. Archive each post on Instagram
4. Download all media files locally
5. Save comprehensive metadata

### Test With Single Post

To test the archiver with a single post:
```bash
python -m src.instagram_archiver <post_url_or_id>
```

Example:
```bash
# Using full URL
python -m src.instagram_archiver https://www.instagram.com/p/ABC123xyz/

# Using just the post ID/shortcode
python -m src.instagram_archiver ABC123xyz
```

This will:
1. Archive only the specified post
2. Download its media files
3. Save its metadata
Perfect for testing the setup before running a full archive.

## Output Structure

```
Instagram_Archive/
├── images/
│   └── YYYYMMDD_HHMMSS_postid.jpg
├── videos/
│   └── YYYYMMDD_HHMMSS_postid.mp4
└── metadata/
    ├── posts_metadata.json
    └── posts_metadata.csv
```

## Metadata Format

The tool stores the following metadata for each post:
- Post ID
- Caption
- Media type
- Timestamp
- Permalink
- Engagement metrics (likes, comments)
- Hashtags
- Location data (if available)
- Local file paths
- Download timestamp

## Error Handling

The tool implements comprehensive error handling:
- Automatic retries for failed requests
- Rate limit management
- Session timeout handling
- Network error recovery
- Detailed logging

## Logging

Logs are stored in the `logs` directory with the following format:
- `instagram_archiver_YYYY-MM-DD.log`

## Security Considerations

- Store your `.env` file securely and never commit it to version control
- Use environment variables for sensitive credentials
- Implement proper token refresh mechanisms
- Follow Instagram's rate limiting guidelines

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for personal use only. Make sure to comply with Instagram's Terms of Service and API usage guidelines when using this tool. 