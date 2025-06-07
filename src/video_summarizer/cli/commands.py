"""
CLI commands for the video summarizer.

This module contains the main command processing logic that orchestrates
the different components of the video summarization pipeline.
"""

import time
from pathlib import Path
from typing import Optional
import json

from rich.progress import Progress, TaskID
from rich.console import Console

from ..models.data_models import (
    VideoSummaryConfig, 
    VideoSummaryResult, 
    VideoMetadata
)
from ..utils.youtube import YouTubeDownloader
from ..utils.file_manager import create_output_filename, create_output_subdirectory, save_result
from ..keyframes.extractor import KeyframeExtractor
from ..audio.extractor import AudioExtractor
from ..audio.transcriber import AudioTranscriber
from ..audio.summarizer import TopicSummarizer
from ..llm.processor import LLMProcessor
from ..utils.markdown_generator import MarkdownGenerator
from video_summarizer.audio.topic_segmenter import segment_topics_with_llm_full

console = Console()


def process_video(
    config: VideoSummaryConfig, 
    progress: Progress, 
    task: TaskID
) -> Path:
    """
    Main function to process a video and generate a summary.
    
    Args:
        config: Configuration for video processing
        progress: Rich progress instance for UI updates
        task: Progress task ID for updates
        
    Returns:
        Path to the generated summary file
    """
    start_time = time.time()
    
    try:
        # Initialize result object
        result = VideoSummaryResult(
            video_metadata=VideoMetadata(
                title="",
                url=config.youtube_url,
                video_id=""
            )
        )
        
        # Stage 1: Download video
        progress.update(task, description="Downloading video...")
        downloader = YouTubeDownloader(config)
        video_path, metadata = downloader.download()
        result.video_metadata = metadata
        
        if config.verbose:
            console.print(f"[OK] Downloaded: {metadata.title}", style="green")
        
        # Create output subdirectory for this processing run
        output_subdir = create_output_subdirectory(config.output_dir, metadata.title, metadata.video_id)
        
        # Stage 2: Extract keyframes
        progress.update(task, description="Extracting keyframes...")
        keyframe_extractor = KeyframeExtractor(config, output_subdir)
        keyframes = keyframe_extractor.extract(video_path)
        result.keyframes = keyframes
        
        if config.verbose:
            console.print(f"[OK] Extracted {len(keyframes)} keyframes", style="green")
        
        # Stage 3: Extract audio
        progress.update(task, description="Extracting audio...")
        audio_extractor = AudioExtractor(config)
        audio_path = audio_extractor.extract(video_path)
        
        if config.verbose:
            console.print(f"[OK] Audio extracted to {audio_path}", style="green")
        
        # Stage 4: Transcribe audio
        if config.include_transcript:
            progress.update(task, description="Transcribing audio...")
            transcriber = AudioTranscriber(config)
            transcript_segments = transcriber.transcribe(audio_path)
            result.transcript_segments = transcript_segments

            # Save transcript segments as JSON
            transcript_json_path = output_subdir / "transcript_segments.json"
            with open(transcript_json_path, "w", encoding="utf-8") as f:
                json.dump([s.model_dump() for s in transcript_segments], f, ensure_ascii=False, indent=2)
            
            if config.verbose:
                console.print(f"[OK] Transcribed {len(transcript_segments)} segments", style="green")

            # Topic segmentation using LLM
            topic_json_path = output_subdir / "topic_segments.json"
            segment_topics_with_llm_full(
                [s.model_dump() for s in transcript_segments],
                output_path=topic_json_path
            )
        
        # Stage 5: Generate topic summaries
        if config.include_topics and result.transcript_segments:
            progress.update(task, description="Analyzing topics...")
            topic_summarizer = TopicSummarizer(config)
            topic_summaries = topic_summarizer.summarize(result.transcript_segments)
            result.topic_summaries = topic_summaries
            
            if config.verbose:
                console.print(f"[OK] Identified {len(topic_summaries)} topics", style="green")
        
        # Stage 6: LLM processing
        progress.update(task, description="Generating AI summary...")
        llm_processor = LLMProcessor(config)
        llm_summary = llm_processor.process(result)
        result.llm_summary = llm_summary
        
        if config.verbose:
            console.print("[OK] AI summary generated", style="green")
        
        # Stage 7: Generate markdown
        progress.update(task, description="Creating markdown file...")
        markdown_generator = MarkdownGenerator(config)
        markdown_content = markdown_generator.generate(result)
        
        # Save the result
        output_filename = create_output_filename(metadata.title, metadata.video_id)
        output_path = output_subdir / output_filename
        save_result(output_path, markdown_content)
        
        result.output_file_path = output_path
        result.processing_time = time.time() - start_time
        
        progress.update(task, description="Processing complete!")
        
        if config.verbose:
            console.print(f"[OK] Total processing time: {result.processing_time:.2f}s", style="green")
        
        # Cleanup temporary files
        _cleanup_temp_files(video_path, audio_path)
        
        return output_path
        
    except Exception as e:
        progress.update(task, description=f"Error: {str(e)}")
        raise


def _cleanup_temp_files(*file_paths: Path):
    """Clean up temporary files created during processing."""
    for file_path in file_paths:
        try:
            if file_path and file_path.exists():
                file_path.unlink()
        except Exception as e:
            console.print(f"[WARNING] Could not delete temp file {file_path}: {e}", style="yellow")


def validate_config(config: VideoSummaryConfig) -> bool:
    """
    Validate the configuration before processing.
    
    Args:
        config: Configuration to validate
        
    Returns:
        True if configuration is valid
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Check if output directory is writable
    try:
        config.output_dir.mkdir(parents=True, exist_ok=True)
        test_file = config.output_dir / ".test_write"
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        raise ValueError(f"Output directory is not writable: {e}")
    
    # Validate API keys if needed
    if config.model.startswith('gpt-') and not config.openai_api_key:
        import os
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OpenAI API key is required for GPT models")
    
    return True 