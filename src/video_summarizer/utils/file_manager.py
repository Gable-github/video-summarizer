"""
File management utilities for the video summarizer.

This module handles file operations, directory management, and output formatting.
"""

import re
from pathlib import Path
from typing import Optional
from datetime import datetime


def ensure_output_directory(output_dir: Path) -> None:
    """
    Ensure the output directory exists and is writable.
    
    Args:
        output_dir: Path to the output directory
        
    Raises:
        PermissionError: If directory cannot be created or is not writable
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Test write permissions
        test_file = output_dir / ".test_write"
        test_file.touch()
        test_file.unlink()
        
    except Exception as e:
        raise PermissionError(f"Cannot create or write to output directory {output_dir}: {e}")


def create_output_filename(video_title: str, video_id: str, extension: str = "md") -> str:
    """
    Create a safe filename for the output file based on video title and ID.
    
    Args:
        video_title: Title of the video
        video_id: YouTube video ID
        extension: File extension (default: md)
        
    Returns:
        Safe filename string
    """
    # Clean the title for use as filename
    safe_title = sanitize_filename(video_title)
    
    # Truncate if too long
    max_title_length = 50
    if len(safe_title) > max_title_length:
        safe_title = safe_title[:max_title_length].rstrip()
    
    # Simple filename without timestamp (timestamp will be in folder name)
    filename = f"{safe_title}_{video_id}.{extension}"
    
    return filename


def create_output_subdirectory(output_dir: Path, video_title: str, video_id: str) -> Path:
    """
    Create a timestamped subdirectory for storing all output files.
    
    Args:
        output_dir: Main output directory
        video_title: Title of the video
        video_id: YouTube video ID
        
    Returns:
        Path to the output subdirectory
    """
    # Clean the title for use as folder name
    safe_title = sanitize_filename(video_title)
    
    # Truncate if too long
    max_title_length = 30
    if len(safe_title) > max_title_length:
        safe_title = safe_title[:max_title_length].rstrip()
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create folder name
    folder_name = f"{safe_title}_{video_id}_{timestamp}"
    output_subdir = output_dir / folder_name
    
    ensure_directory_exists(output_subdir)
    return output_subdir


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    
    Args:
        filename: Original filename string
        
    Returns:
        Sanitized filename string
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Replace spaces and other characters with underscores
    filename = re.sub(r'[\s\-\[\](){}]+', '_', filename)
    
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    
    # Ensure it's not empty
    if not filename:
        filename = "untitled"
    
    return filename


def save_result(output_path: Path, content: str) -> None:
    """
    Save the generated content to a file.
    
    Args:
        output_path: Path where to save the file
        content: Content to save
        
    Raises:
        IOError: If file cannot be written
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        raise IOError(f"Cannot write to file {output_path}: {e}")


def create_temp_directory() -> Path:
    """
    Create a temporary directory for processing files.
    
    Returns:
        Path to the temporary directory
    """
    import tempfile
    
    temp_dir = Path(tempfile.mkdtemp(prefix="video_summarizer_"))
    return temp_dir


def cleanup_temp_directory(temp_dir: Path) -> None:
    """
    Clean up a temporary directory and all its contents.
    
    Args:
        temp_dir: Path to the temporary directory to clean up
    """
    import shutil
    
    try:
        if temp_dir.exists() and temp_dir.is_dir():
            shutil.rmtree(temp_dir)
    except Exception as e:
        # Log warning but don't raise - cleanup failures shouldn't stop the process
        print(f"Warning: Could not clean up temporary directory {temp_dir}: {e}")


def get_file_size_mb(file_path: Path) -> float:
    """
    Get the size of a file in megabytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB
    """
    if not file_path.exists():
        return 0.0
    
    size_bytes = file_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    return round(size_mb, 2)


def ensure_directory_exists(directory: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
    """
    directory.mkdir(parents=True, exist_ok=True)


def copy_file_to_output(source_path: Path, output_dir: Path, new_name: Optional[str] = None) -> Path:
    """
    Copy a file to the output directory with optional renaming.
    
    Args:
        source_path: Source file path
        output_dir: Destination directory
        new_name: Optional new filename
        
    Returns:
        Path to the copied file
    """
    import shutil
    
    ensure_directory_exists(output_dir)
    
    if new_name:
        dest_path = output_dir / new_name
    else:
        dest_path = output_dir / source_path.name
    
    shutil.copy2(source_path, dest_path)
    return dest_path


def create_images_subdirectory(output_subdir: Path) -> Path:
    """
    Create a subdirectory for storing keyframe images within the output subdirectory.
    
    Args:
        output_subdir: The output subdirectory for this processing run
        
    Returns:
        Path to the images subdirectory
    """
    images_dir = output_subdir / "images"
    ensure_directory_exists(images_dir)
    return images_dir 