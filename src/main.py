import os
import sys
from pathlib import Path
import json
from tqdm import tqdm
import time
import signal

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from config import OUTPUT_DIR, DEFAULT_VIEWER_PROFILE
from src.extractors.youtube_extractor import YouTubeExtractor
from src.extractors.whisper_extractor import WhisperExtractor
from src.analyzers.transcript_analyzer import TranscriptAnalyzer
from src.formatters.markdown_formatter import MarkdownFormatter
from src.database.db_handler import DatabaseHandler

class YouTubeAnalyzer:
    def __init__(self):
        self.yt_extractor = YouTubeExtractor()
        self.whisper_extractor = None  # Initialize as None
        self.analyzer = TranscriptAnalyzer()
        self.formatter = MarkdownFormatter()
        self.db_handler = DatabaseHandler()
        self.whisper_cancelled = False

    def _init_whisper(self):
        """Initialize Whisper extractor only when needed."""
        if self.whisper_extractor is None:
            from src.extractors.whisper_extractor import WhisperExtractor
            self.whisper_extractor = WhisperExtractor()

    def signal_handler(self, signum, frame):
        """Handle interrupt signal"""
        self.whisper_cancelled = True
        print("\nWhisper transcription cancelled. Continuing with auto-generated transcript only...")

    def analyze_video(self, url, viewer_profile=None, use_whisper=True):
        """Analyze a YouTube video and generate reports."""
        try:
            if viewer_profile is None:
                viewer_profile = DEFAULT_VIEWER_PROFILE

            # Create progress bar for overall process
            steps = ['Extracting metadata', 'Getting transcripts', 'Analyzing content', 'Saving results']
            with tqdm(total=len(steps), desc="Overall progress", position=0) as pbar:
                print("\nExtracting video ID and metadata...")
                video_id = self.yt_extractor.extract_video_id(url)
                
                # Check if video has been processed before
                if self.db_handler.video_exists(video_id):
                    print(f"Video {video_id} has already been processed.")
                    return
                
                metadata = self.yt_extractor.extract_metadata(url)
                pbar.update(1)
                pbar.set_description(f"Completed: {steps[0]}")

                print("\nGetting auto-generated transcript...")
                auto_transcript = self.yt_extractor.get_auto_transcript(video_id)
                if not auto_transcript:
                    print("Warning: Could not get auto-generated transcript")

                whisper_transcript = None
                if use_whisper:
                    self._init_whisper()  # Initialize Whisper only if needed
                    print("\nGetting Whisper transcript... (Press Ctrl+C to skip)")
                    # Set up signal handler for Ctrl+C
                    signal.signal(signal.SIGINT, self.signal_handler)
                    try:
                        whisper_transcript = self.whisper_extractor.get_whisper_transcript(url)
                    except KeyboardInterrupt:
                        print("\nWhisper transcription cancelled.")
                        whisper_transcript = None
                    finally:
                        # Reset signal handler
                        signal.signal(signal.SIGINT, signal.default_int_handler)

                if not auto_transcript and not whisper_transcript:
                    raise Exception("Could not obtain any transcripts")
                pbar.update(1)
                pbar.set_description(f"Completed: {steps[1]}")

                print("\nComparing and analyzing transcripts...")
                with tqdm(total=2, desc="Analysis progress") as analysis_pbar:
                    transcript_result = self.analyzer.compare_transcripts(
                        auto_transcript, 
                        whisper_transcript
                    )
                    if transcript_result is None:
                        raise Exception("Transcript analysis cancelled by user")
                    analysis_pbar.update(1)

                    analysis = self.analyzer.analyze_content(
                        metadata,
                        transcript_result['text'],
                        viewer_profile
                    )
                    if analysis is None:
                        raise Exception("Content analysis cancelled by user")
                    analysis_pbar.update(1)
                pbar.update(1)
                pbar.set_description(f"Completed: {steps[2]}")

                # Create output directory structure
                video_dir = OUTPUT_DIR / video_id
                video_dir.mkdir(exist_ok=True)

                # Save outputs
                print("\nSaving outputs...")
                transcript_file = video_dir / "transcript.md"
                analysis_file = video_dir / "analysis.md"

                with tqdm(total=3, desc="Saving files") as save_pbar:
                    with open(transcript_file, 'w') as f:
                        f.write(self.formatter.format_transcript(transcript_result))
                    save_pbar.update(1)
                    
                    with open(analysis_file, 'w') as f:
                        f.write(self.formatter.format_analysis(analysis))
                    save_pbar.update(1)

                    # Extract scores and save to database
                    scores = self._extract_scores(analysis)
                    video_data = {
                        'video_id': video_id,
                        'url': url,
                        'metadata': metadata,
                        'transcript_file': str(transcript_file),
                        'analysis_file': str(analysis_file),
                        'info_quality_score': scores['info_quality'],
                        'viewer_interest_score': scores['viewer_interest']
                    }
                    self.db_handler.add_video(video_data)
                    save_pbar.update(1)
                pbar.update(1)
                pbar.set_description(f"Completed: {steps[3]}")

                print("\nAnalysis complete! Check the output directory for results.")

        except Exception as e:
            print(f"\nError during video analysis: {str(e)}")
            raise
        finally:
            self.db_handler.close()

    def _extract_scores(self, analysis):
        """Extract scores from analysis text."""
        # This is a simple implementation - you might want to make it more robust
        try:
            info_quality = int(analysis['info_quality'])
            viewer_interest = int(analysis['viewer_interest'])
            return {
                'info_quality': info_quality,
                'viewer_interest': viewer_interest
            }
        except:
            return {
                'info_quality': 0,
                'viewer_interest': 0
            }

if __name__ == "__main__":
    try:
        analyzer = YouTubeAnalyzer()
        url = input("Enter YouTube URL: ")
        viewer_profile = input("Enter viewer profile (or press Enter for default): ").strip()
        use_whisper = input("Use Whisper for additional transcription? (y/N): ").strip().lower() == 'y'
        
        analyzer.analyze_video(
            url, 
            viewer_profile if viewer_profile else None,
            use_whisper=use_whisper
        )
    except Exception as e:
        print(f"Program terminated with error: {str(e)}") 