"""
Configuration settings for the video summarizer.

This module contains default settings and configuration management.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    
    # Default Processing Settings
    default_quality: str = "medium"
    default_model: str = "gpt-3.5-turbo"
    default_max_keyframes: int = 20
    default_output_dir: str = "./output"
    
    # Video Processing
    max_video_duration: int = 3600  # 1 hour in seconds
    supported_video_formats: list = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    
    # Audio Processing
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    
    # Image Processing
    keyframe_formats: list = ["png", "jpg", "jpeg"]
    default_image_format: str = "png"
    
    # Output Settings
    markdown_template_dir: Optional[str] = None
    include_debug_info: bool = False
    
    # Performance Settings
    max_concurrent_downloads: int = 1
    temp_dir_cleanup: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_prefix = "VIDEO_SUMMARIZER_"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def load_config_from_file(config_path: Path) -> dict:
    """
    Load configuration from a file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary with configuration values
    """
    import json
    import yaml
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    suffix = config_path.suffix.lower()
    
    if suffix == ".json":
        with open(config_path, 'r') as f:
            return json.load(f)
    elif suffix in [".yaml", ".yml"]:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        raise ValueError(f"Unsupported configuration file format: {suffix}")


def validate_api_keys() -> dict:
    """
    Validate that required API keys are available.
    
    Returns:
        Dictionary with validation results
    """
    results = {}
    
    # Check OpenAI API key
    openai_key = settings.openai_api_key or os.getenv('OPENAI_API_KEY')
    results['openai'] = {
        'available': bool(openai_key),
        'key': openai_key[:8] + "..." if openai_key else None
    }
    
    return results 