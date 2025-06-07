#!/usr/bin/env python3
"""
Video Summarizer CLI - Main Entry Point

A CLI tool that processes YouTube videos to create markdown summaries with keyframes.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
from dotenv import load_dotenv

from .cli.commands import process_video
from .utils.file_manager import ensure_output_directory
from .models.data_models import VideoSummaryConfig

console = Console()
load_dotenv()


def print_banner():
    """Print the application banner."""
    banner = Text("Video Summarizer", style="bold blue")
    subtitle = Text("Transform YouTube videos into structured markdown summaries", style="dim")
    
    console.print(Panel.fit(
        f"{banner}\n{subtitle}",
        border_style="blue",
        padding=(1, 2)
    ))


@click.command()
@click.argument('youtube_url', type=str)
@click.option(
    '--output-dir', '-o',
    type=click.Path(path_type=Path),
    default=Path('./output'),
    help='Directory to save the generated summary (default: ./output)'
)
@click.option(
    '--quality', '-q',
    type=click.Choice(['low', 'medium', 'high']),
    default='medium',
    help='Quality level for keyframe extraction (default: medium)'
)
@click.option(
    '--model', '-m',
    type=str,
    default='gpt-3.5-turbo',
    help='LLM model to use for summarization (default: gpt-3.5-turbo)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
@click.option(
    '--open-result', '--open',
    is_flag=True,
    help='Automatically open the result file after processing'
)
@click.option(
    '--config-file', '-c',
    type=click.Path(exists=True, path_type=Path),
    help='Path to configuration file'
)
def main(
    youtube_url: str,
    output_dir: Path,
    quality: str,
    model: str,
    verbose: bool,
    open_result: bool,
    config_file: Optional[Path]
):
    """
    Process a YouTube video and generate a markdown summary with keyframes.
    
    YOUTUBE_URL: The YouTube video URL to process
    """
    try:
        print_banner()
        
        # Validate YouTube URL
        if not _is_valid_youtube_url(youtube_url):
            console.print("[ERROR] Invalid YouTube URL provided", style="red")
            sys.exit(1)
        
        # Create configuration
        config = VideoSummaryConfig(
            youtube_url=youtube_url,
            output_dir=output_dir,
            quality=quality,
            model=model,
            verbose=verbose,
            open_result=open_result,
            config_file=config_file
        )
        
        # Ensure output directory exists
        ensure_output_directory(output_dir)
        
        # Process the video
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Initializing...", total=None)
            
            result_path = process_video(config, progress, task)
        
        # Success message
        console.print(f"\n[SUCCESS] Summary generated successfully!", style="green bold")
        console.print(f"Output file: {result_path}", style="blue")
        
        if open_result:
            _open_file(result_path)
            
    except KeyboardInterrupt:
        console.print("\n[INTERRUPTED] Process interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[ERROR] {str(e)}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)


def _is_valid_youtube_url(url: str) -> bool:
    """Validate if the provided URL is a valid YouTube URL."""
    youtube_domains = [
        'youtube.com',
        'youtu.be',
        'www.youtube.com',
        'm.youtube.com'
    ]
    return any(domain in url.lower() for domain in youtube_domains)


def _open_file(file_path: Path):
    """Open the generated file with the default system application."""
    import subprocess
    import platform
    
    try:
        if platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', str(file_path)])
        elif platform.system() == 'Windows':
            subprocess.run(['start', str(file_path)], shell=True)
        else:  # Linux
            subprocess.run(['xdg-open', str(file_path)])
        
        console.print(f"Opened {file_path.name} in default application", style="green")
    except Exception as e:
        console.print(f"[WARNING] Could not open file automatically: {e}", style="yellow")


if __name__ == '__main__':
    main() 