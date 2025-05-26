"""
Keyframe extraction module using EAST text detection.

This module implements keyframe extraction based on text detection using the EAST model.
The approach focuses on extracting information-dense frames containing significant text content.
"""

import os
import json
from pathlib import Path
from typing import List
import cv2
import numpy as np
from tqdm import tqdm
from PIL import Image
import imagehash

from ..models.data_models import VideoSummaryConfig, Keyframe
from ..utils.file_manager import create_images_subdirectory


class KeyframeExtractor:
    """
    Keyframe extractor using EAST text detection model.
    
    This implementation focuses on extracting frames with significant text content,
    making it ideal for lecture videos, presentations, and educational content.
    """
    
    def __init__(self, config: VideoSummaryConfig, output_subdir: Path):
        """
        Initialize the keyframe extractor.
        
        Args:
            config: Configuration for video processing
            output_subdir: Output subdirectory for this processing run
        """
        self.config = config
        self.output_subdir = output_subdir
        self.east_model_path = Path(__file__).parent.parent / "models" / "frozen_east_text_detection.pb"
        
        # Verify EAST model exists
        if not self.east_model_path.exists():
            raise FileNotFoundError(f"EAST model not found at: {self.east_model_path}")
    
    def extract(self, video_path: Path) -> List[Keyframe]:
        """
        Extract keyframes from a video file using EAST text detection.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            List of extracted keyframes with text content
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        try:
            # Create output directory for images
            images_dir = create_images_subdirectory(self.output_subdir)
            
            # Run EAST text frame extraction
            saved_metadata = self._east_text_frame_extraction(
                str(video_path),
                str(self.east_model_path),
                images_dir,
                frame_skip=240,  # Process every 240th frame
                confThreshold=0.6  # Confidence threshold for text detection
            )
            
            # Convert metadata to Keyframe objects
            keyframes = self._convert_to_keyframes(saved_metadata, video_path.name)
            
            if self.config.verbose:
                print(f"[OK] Extracted {len(keyframes)} keyframes using EAST text detection")
            
            return keyframes
            
        except Exception as e:
            raise Exception(f"Keyframe extraction failed: {str(e)}")
    
    def _east_text_frame_extraction(self, input_mp4: str, east_model_path: str, 
                                   images_dir: Path, frame_skip: int = 240, 
                                   confThreshold: float = 0.6) -> List[dict]:
        """
        Extract frames with significant text content using EAST model.
        
        Args:
            input_mp4: Path to input video file
            east_model_path: Path to EAST model file
            images_dir: Directory to save extracted frames
            frame_skip: Number of frames to skip between processing
            confThreshold: Confidence threshold for text detection
            
        Returns:
            List of metadata dictionaries for saved frames
        """
        # Load EAST model
        net = cv2.dnn.readNet(east_model_path)
        video = cv2.VideoCapture(input_mp4)
        
        if not video.isOpened():
            raise Exception(f"Could not open video file: {input_mp4}")
        
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frame_id = 0
        saved_metadata = []
        pbar = tqdm(total=total_frames // frame_skip, desc="Extracting keyframes")
        
        # Variables for similarity detection
        prev_hash = None
        last_similar = None
        hash_thresh = 15  # Threshold for perceptual hash similarity
        
        def save_frame_and_metadata(frame, fid):
            """Save frame to disk and record metadata."""
            frame_filename = f"frame_{fid:05d}.jpg"
            frame_path = images_dir / frame_filename
            cv2.imwrite(str(frame_path), frame)
            timestamp = fid / fps
            saved_metadata.append({
                "frame_id": frame_filename,
                "frame_number": fid,
                "timestamp": timestamp,
                "source_video": os.path.basename(input_mp4),
                "frame_path": str(frame_path)
            })
        
        try:
            while video.isOpened():
                # Skip frames according to frame_skip parameter
                if frame_id % frame_skip != 0:
                    if not video.grab():
                        break
                    frame_id += 1
                    continue
                
                ret, frame = video.read()
                if not ret:
                    break
                
                # Resize frame for EAST processing
                newW, newH = 320, 320
                frame_resized = cv2.resize(frame, (newW, newH))
                
                # Prepare input blob for EAST
                blob = cv2.dnn.blobFromImage(
                    frame_resized, 1.0, (newW, newH),
                    (123.68, 116.78, 103.94), swapRB=True, crop=False
                )
                net.setInput(blob)
                
                # Forward pass through EAST
                (scores, geometry) = net.forward([
                    "feature_fusion/Conv_7/Sigmoid", 
                    "feature_fusion/concat_3"
                ])
                
                # Decode text detection predictions
                rects, confidences = self._decode_predictions(
                    scores, geometry, confThreshold=confThreshold
                )
                
                # Only process frames with significant text content (>50 text regions)
                if len(rects) > 50:
                    # Calculate perceptual hash for similarity detection
                    frame_hash = self._get_phash(frame)
                    
                    if prev_hash is None:
                        # First frame with text
                        prev_hash = frame_hash
                        last_similar = (frame, frame_id)
                    elif abs(frame_hash - prev_hash) <= hash_thresh:
                        # Similar to previous frame, update to latest
                        last_similar = (frame, frame_id)
                    else:
                        # Different from previous, save the last similar frame
                        if last_similar:
                            save_frame_and_metadata(*last_similar)
                        prev_hash = frame_hash
                        last_similar = (frame, frame_id)
                
                pbar.update(1)
                frame_id += 1
            
            # Save final frame if needed
            if last_similar:
                save_frame_and_metadata(*last_similar)
                
        finally:
            pbar.close()
            video.release()
        
        return saved_metadata
    
    def _decode_predictions(self, scores, geometry, confThreshold: float = 0.5):
        """
        Decode EAST model predictions to get text bounding boxes.
        
        Args:
            scores: EAST model score output
            geometry: EAST model geometry output
            confThreshold: Confidence threshold for detections
            
        Returns:
            Tuple of (rectangles, confidences)
        """
        (numRows, numCols) = scores.shape[2:4]
        rects = []
        confidences = []
        
        for y in range(0, numRows):
            scoresData = scores[0, 0, y]
            xData0 = geometry[0, 0, y]
            xData1 = geometry[0, 1, y]
            xData2 = geometry[0, 2, y]
            xData3 = geometry[0, 3, y]
            anglesData = geometry[0, 4, y]
            
            for x in range(0, numCols):
                if scoresData[x] < confThreshold:
                    continue
                
                offsetX, offsetY = (x * 4.0, y * 4.0)
                angle = anglesData[x]
                cos = np.cos(angle)
                sin = np.sin(angle)
                h = xData0[x] + xData2[x]
                w = xData1[x] + xData3[x]
                endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
                endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
                startX = int(endX - w)
                startY = int(endY - h)
                
                rects.append((startX, startY, endX, endY))
                confidences.append(float(scoresData[x]))
        
        return (rects, confidences)
    
    def _get_phash(self, frame):
        """
        Calculate perceptual hash of a frame for similarity detection.
        
        Args:
            frame: OpenCV frame (BGR format)
            
        Returns:
            Perceptual hash object
        """
        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        pil_img = pil_img.convert('L').resize((256, 256))
        return imagehash.phash(pil_img)
    
    def _convert_to_keyframes(self, metadata_list: List[dict], source_video: str) -> List[Keyframe]:
        """
        Convert metadata list to Keyframe objects.
        
        Args:
            metadata_list: List of frame metadata dictionaries
            source_video: Source video filename
            
        Returns:
            List of Keyframe objects
        """
        keyframes = []
        
        for metadata in metadata_list:
            keyframe = Keyframe(
                timestamp=metadata["timestamp"],
                image_path=Path(metadata["frame_path"]),
                description=f"Text-rich frame detected at {metadata['timestamp']:.2f}s",
                confidence_score=0.8,  # Hardcoded as requested
                source_video=source_video
            )
            keyframes.append(keyframe)
        
        return keyframes


# TODO: Replace this entire module with the keyframe extraction team's implementation
# The team should provide:
# 1. Advanced keyframe detection algorithms (scene change detection, etc.)
# 2. Better quality assessment for keyframes
# 3. Optimized extraction based on video content
# 4. Support for different video formats and codecs 