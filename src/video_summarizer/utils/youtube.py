"""
YouTube video downloading utilities.

This module handles downloading videos from YouTube using yt-dlp.
"""

import re
from pathlib import Path
from typing import Tuple, Optional

import yt_dlp

from ..models.data_models import VideoSummaryConfig, VideoMetadata
from .file_manager import create_temp_directory


class YouTubeDownloader:
    """Handles downloading videos from YouTube."""
    
    def __init__(self, config: VideoSummaryConfig):
        """
        Initialize the YouTube downloader.
        
        Args:
            config: Configuration for video processing
        """
        self.config = config
        self.temp_dir = create_temp_directory()
    
    def download(self) -> Tuple[Path, VideoMetadata]:
        """
        Download a video from YouTube.
        
        Returns:
            Tuple of (video_file_path, video_metadata)
            
        Raises:
            Exception: If download fails
        """
        # Extract video ID from URL
        video_id = self._extract_video_id(self.config.youtube_url)
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best[height<=720]',  # Limit quality for faster processing
            'outtmpl': str(self.temp_dir / f'{video_id}.%(ext)s'),
            'writeinfojson': True,
            'writesubtitles': False,
            'writeautomaticsub': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(self.config.youtube_url, download=False)
                
                # Create metadata object
                metadata = VideoMetadata(
                    title=info.get('title', 'Unknown Title'),
                    description=info.get('description', ''),
                    duration=info.get('duration'),
                    upload_date=info.get('upload_date'),
                    uploader=info.get('uploader', ''),
                    view_count=info.get('view_count'),
                    url=self.config.youtube_url,
                    video_id=video_id,
                    thumbnail_url=info.get('thumbnail')
                )
                
                # Download the video
                ydl.download([self.config.youtube_url])
                
                # Find the downloaded video file
                video_files = list(self.temp_dir.glob(f'{video_id}.*'))
                video_files = [f for f in video_files if not f.suffix == '.info.json']
                
                if not video_files:
                    raise Exception("Video file not found after download")
                
                video_path = video_files[0]
                
                return video_path, metadata
                
        except Exception as e:
            raise Exception(f"Failed to download video: {str(e)}")
    
    def _extract_video_id(self, url: str) -> str:
        """
        Extract video ID from YouTube URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID string
            
        Raises:
            ValueError: If video ID cannot be extracted
        """
        # Pattern for various YouTube URL formats
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    def get_video_info(self, url: str) -> dict:
        """
        Get video information without downloading.
        
        Args:
            url: YouTube URL
            
        Returns:
            Dictionary with video information
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")
    
    def cleanup(self):
        """Clean up temporary files."""
        from .file_manager import cleanup_temp_directory
        cleanup_temp_directory(self.temp_dir) 