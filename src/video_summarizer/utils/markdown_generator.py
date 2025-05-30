"""
Markdown generation utilities.

This module generates the final markdown output combining all processed data.
"""

from datetime import datetime
from pathlib import Path
from typing import List

from ..models.data_models import VideoSummaryConfig, VideoSummaryResult


class MarkdownGenerator:
    """Generates markdown output from video summary results."""
    
    def __init__(self, config: VideoSummaryConfig):
        """
        Initialize the markdown generator.
        
        Args:
            config: Configuration for video processing
        """
        self.config = config
    
    def generate(self, result: VideoSummaryResult) -> str:
        """
        Generate a complete markdown document from the video summary result.
        
        Args:
            result: Complete video summary result
            
        Returns:
            Formatted markdown content
        """
        sections = []
        
        # Header and metadata
        sections.append(self._generate_header(result))
        sections.append(self._generate_metadata(result))
        
        # Table of contents
        sections.append(self._generate_toc(result))
        
        # Executive summary
        if result.llm_summary:
            sections.append(self._generate_executive_summary(result.llm_summary.executive_summary))
        
        # Key insights
        if result.llm_summary and result.llm_summary.key_insights:
            sections.append(self._generate_key_insights(result.llm_summary.key_insights))
        
        # Keyframes section
        if result.keyframes and self.config.include_images:
            sections.append(self._generate_keyframes_section(result.keyframes))
        
        # Topics section
        if result.topic_summaries:
            sections.append(self._generate_topics_section(result.topic_summaries))
        
        # Detailed summary
        if result.llm_summary:
            sections.append(self._generate_detailed_summary(result.llm_summary.detailed_summary))
        
        # Transcript section
        if result.transcript_segments and self.config.include_transcript:
            sections.append(self._generate_transcript_section(result.transcript_segments))
        
        # Recommendations
        if result.llm_summary and result.llm_summary.recommendations:
            sections.append(self._generate_recommendations(result.llm_summary.recommendations))
        
        # Footer
        sections.append(self._generate_footer(result))
        
        return "\n\n".join(sections)
    
    def _generate_header(self, result: VideoSummaryResult) -> str:
        """Generate the document header."""
        title = result.video_metadata.title
        return f"""# Video Summary: {title}

> **Generated by Video Summarizer** | {datetime.now().strftime("%B %d, %Y at %I:%M %p")}"""
    
    def _generate_metadata(self, result: VideoSummaryResult) -> str:
        """Generate video metadata section."""
        metadata = result.video_metadata
        duration_str = self._format_duration(metadata.duration) if metadata.duration else "Unknown"
        
        lines = [
            "## Video Information",
            "",
            f"- **Title:** {metadata.title}",
            f"- **URL:** [{metadata.url}]({metadata.url})",
            f"- **Duration:** {duration_str}",
        ]
        
        if metadata.uploader:
            lines.append(f"- **Channel:** {metadata.uploader}")
        
        if metadata.upload_date:
            lines.append(f"- **Upload Date:** {metadata.upload_date}")
        
        if metadata.view_count:
            lines.append(f"- **Views:** {metadata.view_count:,}")
        
        return "\n".join(lines)
    
    def _generate_toc(self, result: VideoSummaryResult) -> str:
        """Generate table of contents."""
        lines = [
            "## Table of Contents",
            "",
            "1. [Executive Summary](#executive-summary)",
            "2. [Key Insights](#key-insights)",
        ]
        
        section_num = 3
        
        if result.keyframes and self.config.include_images:
            lines.append(f"{section_num}. [Key Moments (Keyframes)](#key-moments-keyframes)")
            section_num += 1
        
        if result.topic_summaries:
            lines.append(f"{section_num}. [Topics Overview](#topics-overview)")
            section_num += 1
        
        lines.append(f"{section_num}. [Detailed Summary](#detailed-summary)")
        section_num += 1
        
        if result.transcript_segments and self.config.include_transcript:
            lines.append(f"{section_num}. [Full Transcript](#full-transcript)")
            section_num += 1
        
        if result.llm_summary and result.llm_summary.recommendations:
            lines.append(f"{section_num}. [Recommendations](#recommendations)")
        
        return "\n".join(lines)
    
    def _generate_executive_summary(self, summary: str) -> str:
        """Generate executive summary section."""
        return f"""## Executive Summary

{summary}"""
    
    def _generate_key_insights(self, insights: List[str]) -> str:
        """Generate key insights section."""
        lines = [
            "## Key Insights",
            ""
        ]
        
        for insight in insights:
            lines.append(f"- {insight}")
        
        return "\n".join(lines)
    
    def _generate_keyframes_section(self, keyframes) -> str:
        """Generate keyframes section."""
        lines = [
            "## Key Moments (Keyframes)",
            "",
            "Visual highlights from the video with timestamps:",
            ""
        ]
        
        for i, keyframe in enumerate(keyframes, 1):
            timestamp_str = self._format_timestamp(keyframe.timestamp)
            relative_path = Path(keyframe.image_path).name
            
            lines.extend([
                f"### {i}. {timestamp_str}",
                "",
                f"![Keyframe {i}](images/{relative_path})",
                "",
                f"**Description:** {keyframe.description or 'Key moment in the video'}",
                ""
            ])
        
        return "\n".join(lines)
    
    def _generate_topics_section(self, topics) -> str:
        """Generate topics overview section."""
        lines = [
            "## Topics Overview",
            "",
            "Main topics covered in the video:",
            ""
        ]
        
        for i, topic in enumerate(topics, 1):
            start_time = self._format_timestamp(topic.start_time)
            end_time = self._format_timestamp(topic.end_time)
            
            lines.extend([
                f"### {i}. {topic.topic}",
                f"**Time Range:** {start_time} - {end_time}",
                "",
                topic.summary,
                ""
            ])
            
            if topic.key_points:
                lines.append("**Key Points:**")
                for point in topic.key_points:
                    lines.append(f"- {point}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_detailed_summary(self, detailed_summary: str) -> str:
        """Generate detailed summary section."""
        return f"""## Detailed Summary

{detailed_summary}"""
    
    def _generate_transcript_section(self, segments) -> str:
        """Generate transcript section."""
        lines = [
            "## Full Transcript",
            "",
            "Complete transcript with timestamps:",
            ""
        ]
        
        for segment in segments:
            start_time = self._format_timestamp(segment.start_time)
            end_time = self._format_timestamp(segment.end_time)
            
            lines.extend([
                f"**[{start_time} - {end_time}]**",
                segment.text,
                ""
            ])
        
        return "\n".join(lines)
    
    def _generate_recommendations(self, recommendations: List[str]) -> str:
        """Generate recommendations section."""
        lines = [
            "## Recommendations",
            ""
        ]
        
        for rec in recommendations:
            lines.append(f"- {rec}")
        
        return "\n".join(lines)
    
    def _generate_footer(self, result: VideoSummaryResult) -> str:
        """Generate document footer."""
        processing_time = f"{result.processing_time:.2f} seconds" if result.processing_time else "Unknown"
        
        lines = [
            "---",
            "",
            "## Processing Information",
            "",
            f"- **Generated on:** {result.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Processing time:** {processing_time}",
            f"- **Quality setting:** {self.config.quality}",
            f"- **Model used:** {self.config.model}",
            "",
            "*This summary was automatically generated by Video Summarizer.*"
        ]
        
        return "\n".join(lines)
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human-readable format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp in seconds to MM:SS format."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}" 