# YouTube Video Analyzer

This project analyzes YouTube videos by:
1. Extracting metadata (title, description, top comments)
2. Getting both auto-generated and Whisper-generated transcripts
3. Comparing and correcting transcripts using AI
4. Analyzing content for specific viewer profiles
5. Generating formatted Markdown reports

## Features
- Dual transcript generation (YouTube auto-generated + Whisper)
- AI-powered transcript comparison and correction
- Content analysis tailored to specific viewer profiles
- Progress tracking for long-running operations
- SQLite database for tracking processed videos
- Markdown-formatted output files
- Cleanup of temporary files

## Prerequisites
- Python 3.10 or higher
- FFmpeg installed on your system
- OpenAI API key
- Sufficient disk space for temporary audio files

## Installation

1. Clone the repository:
   git clone https://

2. Install FFmpeg:
   - macOS: brew install ffmpeg
   - Ubuntu/Debian: sudo apt-get install ffmpeg
   - Windows: Download from ffmpeg.org

3. Install Python requirements:
   pip install -r requirements.txt

4. Create a .env file in the root directory with your OpenAI API key:
   OPENAI_API_KEY=your_api_key_here

## Usage

1. Run the analyzer:
   python run.py

2. When prompted:
   - Enter a YouTube URL
   - (Optional) Enter a viewer profile (default: "the average humanist/idealist AI technology enthusiast")
   - Choose whether to use Whisper for additional transcription (y/N)

3. The script will:
   - Download and process the audio
   - Generate YouTube auto-generated transcript
   - (Optional) Generate Whisper transcript (can be cancelled with Ctrl+C)
   - Analyze the content
   - Save results to the database
   - Create markdown files in the output/{video_id}/ directory

## Output Structure

The analyzer creates two main outputs for each video:

1. Markdown files in output/{video_id}/:
   - transcript.md: Combined and corrected transcript
   - analysis.md: Content analysis and insights

2. Database entries in data/videos.db containing:
   - Video metadata
   - File paths
   - Quality scores
   - Processing timestamps

The analysis includes:
- Salient points for the target viewer
- Counterfactual viewpoints
- Bias assessment
- Claims requiring review
- Information quality score (1-10)
- Viewer interest score (1-10)

## Progress Tracking

The analyzer provides real-time progress information for:
- Overall process status
- Audio download progress
- Whisper transcription with ETA
- Analysis steps
- File saving operations

## Error Handling

The system includes robust error handling:
- Automatic cleanup of temporary files
- Graceful handling of missing transcripts
- Database transaction rollback on errors
- Detailed error messages
- Safe termination on interruption

## Database Features

- SQLite database for persistent storage
- Tracks all processed videos
- Prevents duplicate processing
- Stores metadata and analysis results
- Easy access to historical analyses

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[MIT License or your chosen license]