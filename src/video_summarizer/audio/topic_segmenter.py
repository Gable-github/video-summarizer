"""
Topic segmentation module using LLM.

This module provides functionality to segment video transcripts into meaningful topics
using OpenAI's GPT models.
"""

from typing import List
import json
from pathlib import Path

from instructor import patch, OpenAISchema
from openai import OpenAI


class TopicSegment(OpenAISchema):
    """Represents a single topic segment in a video transcript."""
    
    topic: str
    start_time: int
    end_time: int
    summary: str


class TopicSegmentationResult(OpenAISchema):
    """Container for the complete topic segmentation result."""
    
    segments: List[TopicSegment]


def segment_topics_with_llm_full(
    transcript_segments: List[dict],
    output_path: Path
) -> List[TopicSegment]:
    """
    Segment video transcript into topics using LLM.
    
    Args:
        transcript_segments: List of transcript segments with timestamps and text
        output_path: Path to save the segmentation results
        
    Returns:
        List of topic segments with summaries
    """
    client = patch(OpenAI())
    
    system_prompt = """
        You are an expert at analyzing video transcripts and segmenting them into meaningful topics.

        Your task is to:
        1. Read the entire transcript (via `text` field)
        2. Identify the main topics or sections discussed in the video, based on your understanding of the video context.
        3. For each topic, provide:
        - topic: a concise, descriptive topic header under `summary` field
        - start_time: the start time (in seconds) of this topic - get this from the very first `start_time` field of the first segment in the topic
        - end_time: the end time (in seconds) of this topic - get this from the very last `end_time` field of the last segment in the topic
        - summary: a 2–4 sentence summary of what is discussed in this topic

        Output your answer as a JSON array of objects, each with the keys: topic, start_time, end_time, summary.

        Ensure that the end_time of each topic exactly matches the start_time of the next topic, with no gaps or overlaps. All times should be integers.

        Output format example:
        [{"topic": "...", "start_time": 0.0, "end_time": 120.0, "summary": "..."}]
    """

    user_prompt = f"Here is the transcript to analyze:\n{json.dumps(transcript_segments, ensure_ascii=False)}"

    result = client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        response_model=TopicSegmentationResult,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_retries=3,
    )

    # Post-process to ensure contiguous integer times
    segments = [s.model_dump() for s in result.segments]
    segments = sorted(segments, key=lambda t: t["start_time"])
    for i, seg in enumerate(segments):
        seg["start_time"] = int(seg["start_time"])
        seg["end_time"] = int(seg["end_time"])
        if i > 0:
            seg["start_time"] = segments[i-1]["end_time"]

    # Save results to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
    
    return segments