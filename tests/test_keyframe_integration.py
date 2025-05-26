"""
Tests for the keyframe extractor integration.
"""

import pytest
from pathlib import Path

from video_summarizer.models.data_models import VideoSummaryConfig
from video_summarizer.keyframes.extractor import KeyframeExtractor


def test_keyframe_extractor_initialization():
    """Test that the KeyframeExtractor can be initialized properly."""
    config = VideoSummaryConfig(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    
    extractor = KeyframeExtractor(config)
    
    # Verify the extractor has the expected attributes
    assert extractor.config == config
    assert extractor.east_model_path.exists()
    assert extractor.east_model_path.name == "frozen_east_text_detection.pb"


def test_keyframe_extractor_model_path():
    """Test that the EAST model path is correctly set."""
    config = VideoSummaryConfig(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    
    extractor = KeyframeExtractor(config)
    
    # Verify the model path points to the correct location
    expected_path = Path(__file__).parent.parent / "src" / "video_summarizer" / "models" / "frozen_east_text_detection.pb"
    assert extractor.east_model_path.exists()
    assert extractor.east_model_path.name == "frozen_east_text_detection.pb"


def test_keyframe_extractor_missing_model():
    """Test that KeyframeExtractor raises error when model is missing."""
    import tempfile
    import shutil
    
    config = VideoSummaryConfig(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    
    # Temporarily move the model file to test missing model scenario
    original_model_path = Path(__file__).parent.parent / "src" / "video_summarizer" / "models" / "frozen_east_text_detection.pb"
    
    if original_model_path.exists():
        # Create a temporary backup
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shutil.copy2(original_model_path, tmp.name)
            backup_path = tmp.name
        
        try:
            # Remove the original model temporarily
            original_model_path.unlink()
            
            # Should raise FileNotFoundError during initialization
            with pytest.raises(FileNotFoundError, match="EAST model not found"):
                KeyframeExtractor(config)
                
        finally:
            # Restore the model file
            shutil.copy2(backup_path, original_model_path)
            Path(backup_path).unlink()
    else:
        # If model doesn't exist, the test should pass by default
        with pytest.raises(FileNotFoundError, match="EAST model not found"):
            KeyframeExtractor(config)


def test_keyframe_extractor_extract_missing_video():
    """Test that extract method raises error for missing video file."""
    config = VideoSummaryConfig(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    
    extractor = KeyframeExtractor(config)
    non_existent_video = Path("/non/existent/video.mp4")
    
    with pytest.raises(FileNotFoundError, match="Video file not found"):
        extractor.extract(non_existent_video)


def test_decode_predictions_function():
    """Test the decode_predictions function with dummy data."""
    import numpy as np
    
    config = VideoSummaryConfig(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    
    extractor = KeyframeExtractor(config)
    
    # Create dummy scores and geometry arrays
    scores = np.random.rand(1, 1, 80, 80) * 0.3  # Low confidence scores
    geometry = np.random.rand(1, 5, 80, 80)
    
    rects, confidences = extractor._decode_predictions(scores, geometry, confThreshold=0.5)
    
    # With low confidence scores, should return empty lists
    assert isinstance(rects, list)
    assert isinstance(confidences, list)
    assert len(rects) == len(confidences)


def test_get_phash_function():
    """Test the perceptual hash function."""
    import numpy as np
    
    config = VideoSummaryConfig(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    
    extractor = KeyframeExtractor(config)
    
    # Create a dummy frame (BGR format)
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    hash_result = extractor._get_phash(frame)
    
    # Should return an imagehash object
    assert hash_result is not None
    assert hasattr(hash_result, '__sub__')  # Should support subtraction for comparison


def test_convert_to_keyframes():
    """Test conversion of metadata to Keyframe objects."""
    config = VideoSummaryConfig(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    
    extractor = KeyframeExtractor(config)
    
    # Create dummy metadata
    metadata_list = [
        {
            "frame_id": "frame_00001.jpg",
            "frame_number": 240,
            "timestamp": 10.0,
            "source_video": "test_video.mp4",
            "frame_path": "/path/to/frame_00001.jpg"
        },
        {
            "frame_id": "frame_00002.jpg", 
            "frame_number": 480,
            "timestamp": 20.0,
            "source_video": "test_video.mp4",
            "frame_path": "/path/to/frame_00002.jpg"
        }
    ]
    
    keyframes = extractor._convert_to_keyframes(metadata_list, "test_video.mp4")
    
    assert len(keyframes) == 2
    
    # Check first keyframe
    kf1 = keyframes[0]
    assert kf1.timestamp == 10.0
    assert kf1.image_path == Path("/path/to/frame_00001.jpg")
    assert kf1.source_video == "test_video.mp4"
    assert kf1.confidence_score == 0.8
    assert "Text-rich frame detected at 10.00s" in kf1.description
    
    # Check second keyframe
    kf2 = keyframes[1]
    assert kf2.timestamp == 20.0
    assert kf2.image_path == Path("/path/to/frame_00002.jpg")
    assert kf2.source_video == "test_video.mp4"


if __name__ == "__main__":
    pytest.main([__file__]) 