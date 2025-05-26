# Video Summarizer

A CLI tool that transforms YouTube videos into structured markdown summaries with keyframes, transcripts, and quick summaries. Great for quickly understanding lecture-style videos, keynotes, and other information-dense content.

## Current Status

**Phase 1: Complete**
- ✓ Project structure and CLI framework
- ✓ **Team 1 Integration Complete**: EAST text detection for keyframe extraction
- ○ **Team 2**: Audio processing (awaiting integration)
- ○ **Team 3**: LLM processing (awaiting integration)

## Features

- **YouTube Integration**: Download videos directly from YouTube URLs
- **Smart Keyframe Extraction**: Uses EAST text detection model to identify slides and presentation content
- **Audio Processing**: Extract and transcribe audio with timestamps *(coming soon)*
- **Topic Analysis**: Identify and summarize key topics discussed in chronological order *(coming soon)*
- **AI Summarization**: Generate comprehensive topical and overall summaries using LLMs *(coming soon)*
- **Markdown Output**: Structured markdown reports with embedded keyframes
- **Progress Tracking**: CLI with progress bars and status updates
- **Configurable**: User-defined settings for different use cases

## Quick Start

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd video-summarizer
   ```

2. **Set up the environment**:
   ```bash
   # Install uv if you don't have it
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create and activate environment
   uv sync
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

3. **Install the package**:
   ```bash
   uv pip install -e .
   ```

### Basic Usage

```bash
# Process a YouTube video
video-summarizer "https://www.youtube.com/watch?v=VIDEO_ID"

# With custom options
video-summarizer "https://www.youtube.com/watch?v=VIDEO_ID" \
  --output-dir ./my-summaries \
  --quality high \
  --verbose \
  --open
```

### Command Options

- `--output-dir, -o`: Directory to save the generated summary (default: ./output)
- `--quality, -q`: Quality level for keyframe extraction (low/medium/high)
- `--verbose, -v`: Enable verbose logging
- `--open`: Automatically open the result file after processing
- `--config-file, -c`: Path to configuration file

## Team Integration Status

### Team 1: Keyframe Extraction (COMPLETE)
- **Status**: Fully integrated with EAST text detection
- **Location**: `src/video_summarizer/keyframes/`
- **Technology**: EAST (Efficient and Accurate Scene Text) detection model
- **Features**:
  - Detects text-rich frames (slides, presentations)
  - Perceptual hashing to avoid duplicates
  - Configurable confidence thresholds
  - Processes every 240th frame for efficiency (configurable in config.py)

### Team 2: Audio Processing (PENDING)
- **Status**: Placeholder implementation ready for integration
- **Location**: `src/video_summarizer/audio/`
- **Example Interface**: 
  - `AudioExtractor.extract(video_path) -> Path`
  - `AudioTranscriber.transcribe(audio_path) -> List[TranscriptSegment]`
  - `TopicSummarizer.summarize(segments) -> List[TopicSummary]`

### Team 3: LLM Processing (PENDING)
- **Status**: Placeholder implementation ready for integration
- **Location**: `src/video_summarizer/llm/`
- **Example Interface**: `LLMProcessor.process(result) -> LLMSummary` (subject to change)

## Project Structure

```
video-summarizer/
├── src/video_summarizer/          # Main package
│   ├── cli/                       # CLI interface
│   ├── keyframes/                 # [COMPLETE] Keyframe extraction (Team 1)
│   ├── audio/                     # [PENDING] Audio processing (Team 2)
│   ├── llm/                       # [PENDING] LLM processing (Team 3)
│   ├── utils/                     # Utilities
│   └── models/                    # Data models & EAST detection model
├── config/                        # Configuration files
├── output/                        # Generated summaries (gitignored)
├── temp/                          # Temporary files
├── tests/                         # Test suite (17 tests, all passing)
└── docs/                          # Documentation
```

## Current Output

With Team 1 integrated, the tool currently generates:

- **Video metadata** (title, duration, channel, etc.)
- **Smart keyframes** extracted using EAST text detection
- **Keyframe gallery** with timestamps in markdown
- **Processing statistics** (frames analyzed, keyframes found, etc.)

*Coming soon with Teams 2 & 3*:
- Audio transcription with timestamps
- Topic analysis and summaries (chronological order, grouped by topic)
- LLM-generated topical and overall summaries

## Configuration

### Environment Variables

Create a `.env` file with your configuration:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### Configuration File

You can also use a JSON configuration file for specific video processing settings (to be implemented later):

```json
{
  "quality": "high",
  "max_keyframes": 30,
  "confidence_threshold": 0.6,
  "frame_skip": 240
}
```

## Development

### Running Tests

```bash
# Run all tests (17 tests currently)
pytest

# Run with coverage
pytest --cov=video_summarizer

# Run specific test file
pytest tests/test_keyframes.py -v
```

### Code Quality

```bash
# Format code
ruff format src/ tests/

# Linting
ruff check src/ tests/

# Type checking
mypy src/
```

## Dependencies

### Core Dependencies
- **click**: CLI framework
- **rich**: Beautiful terminal output
- **pydantic**: Data validation and type safety
- **yt-dlp**: YouTube video downloading
- **opencv-python**: Video processing
- **numpy**: Numerical operations
- **imagehash**: Perceptual hashing for duplicate detection
- **tqdm**: Progress bars

### Development Dependencies
- **pytest**: Testing framework
- **ruff**: Fast Python linter and formatter
- **mypy**: Type checking

## Example Output

```bash
$ video-summarizer "https://www.youtube.com/watch?v=example"

Video Summarizer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Downloading video...
Downloaded: How Netflix Uses Java - 2025 Edition

Extracting keyframes...
Processed 1,234 frames, found 27 keyframes
Processing time: 44.59 seconds

Generating summary...
Summary saved to: output/how-netflix-uses-java-2025-edition.md

Opening result file...
```