"""
Basic tests for the video summarizer package.
"""

import pytest
from pathlib import Path

from video_summarizer.models.data_models import (
    VideoSummaryConfig, 
    VideoMetadata, 
    Keyframe,
    TranscriptSegment,
    TopicSummary,
    LLMSummary,
    VideoSummaryResult
)
from video_summarizer.utils.file_manager import sanitize_filename, create_output_filename


def test_video_summary_config_creation():
    """Test creating a VideoSummaryConfig object."""
    config = VideoSummaryConfig(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    
    assert config.youtube_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert config.quality == "medium"
    assert config.model == "gpt-3.5-turbo"
    assert config.verbose is False
    assert config.max_keyframes == 20


def test_video_metadata_creation():
    """Test creating a VideoMetadata object."""
    metadata = VideoMetadata(
        title="Test Video",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        video_id="dQw4w9WgXcQ",
        duration=180,
        uploader="Test Channel"
    )
    
    assert metadata.title == "Test Video"
    assert metadata.video_id == "dQw4w9WgXcQ"
    assert metadata.duration == 180


def test_keyframe_creation():
    """Test creating a Keyframe object."""
    keyframe = Keyframe(
        timestamp=30.5,
        image_path=Path("test_keyframe.png"),
        description="Test keyframe",
        confidence_score=0.95
    )
    
    assert keyframe.timestamp == 30.5
    assert keyframe.image_path == Path("test_keyframe.png")
    assert keyframe.confidence_score == 0.95


def test_transcript_segment_creation():
    """Test creating a TranscriptSegment object."""
    segment = TranscriptSegment(
        start_time=0.0,
        end_time=30.0,
        text="This is a test transcript segment.",
        confidence=0.92,
        speaker="Speaker 1"
    )
    
    assert segment.start_time == 0.0
    assert segment.end_time == 30.0
    assert segment.text == "This is a test transcript segment."
    assert segment.confidence == 0.92


def test_topic_summary_creation():
    """Test creating a TopicSummary object."""
    topic = TopicSummary(
        topic="Introduction",
        start_time=0.0,
        end_time=60.0,
        summary="This is the introduction section.",
        key_points=["Point 1", "Point 2"],
        relevance_score=0.9
    )
    
    assert topic.topic == "Introduction"
    assert len(topic.key_points) == 2
    assert topic.relevance_score == 0.9


def test_llm_summary_creation():
    """Test creating an LLMSummary object."""
    summary = LLMSummary(
        executive_summary="This is an executive summary.",
        key_insights=["Insight 1", "Insight 2"],
        main_topics=["Topic 1", "Topic 2"],
        detailed_summary="This is a detailed summary.",
        recommendations=["Recommendation 1"]
    )
    
    assert summary.executive_summary == "This is an executive summary."
    assert len(summary.key_insights) == 2
    assert len(summary.main_topics) == 2


def test_video_summary_result_creation():
    """Test creating a VideoSummaryResult object."""
    metadata = VideoMetadata(
        title="Test Video",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        video_id="dQw4w9WgXcQ"
    )
    
    result = VideoSummaryResult(video_metadata=metadata)
    
    assert result.video_metadata.title == "Test Video"
    assert len(result.keyframes) == 0
    assert len(result.transcript_segments) == 0
    assert result.llm_summary is None


def test_sanitize_filename():
    """Test filename sanitization."""
    # Test basic sanitization
    assert sanitize_filename("Hello World") == "Hello_World"
    assert sanitize_filename("Test: Video | Name") == "Test_Video_Name"
    assert sanitize_filename("File<>Name") == "FileName"
    
    # Test edge cases
    assert sanitize_filename("") == "untitled"
    assert sanitize_filename("___") == "untitled"
    assert sanitize_filename("Multiple___Underscores") == "Multiple_Underscores"


def test_create_output_filename():
    """Test output filename creation."""
    filename = create_output_filename("Test Video", "dQw4w9WgXcQ")
    
    assert "Test_Video" in filename
    assert "dQw4w9WgXcQ" in filename
    assert filename.endswith(".md")
    assert len(filename.split("_")) >= 3  # title, video_id, timestamp


def test_youtube_url_validation():
    """Test YouTube URL validation in config."""
    # Valid URLs
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
    ]
    
    for url in valid_urls:
        config = VideoSummaryConfig(youtube_url=url)
        assert config.youtube_url == url
    
    # Invalid URL should raise validation error
    with pytest.raises(ValueError):
        VideoSummaryConfig(youtube_url="https://example.com/video")


if __name__ == "__main__":
    pytest.main([__file__]) 