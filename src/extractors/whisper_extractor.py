import os
import sys
from pathlib import Path
from tqdm import tqdm
import time
from datetime import datetime, timedelta
import signal

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import WHISPER_MODEL

class WhisperExtractor:
    def __init__(self):
        self.model = None
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self._download_progress_hook],
        }
        self.pbar = None
        self.cancelled = False

    def _load_model(self):
        """Lazy load the Whisper model when needed."""
        if self.model is None:
            print("\nLoading Whisper model...")
            # Temporarily redirect stderr to suppress the FutureWarning
            stderr = sys.stderr
            sys.stderr = open(os.devnull, 'w')
            try:
                import whisper
                self.model = whisper.load_model(WHISPER_MODEL)
            finally:
                sys.stderr = stderr

    def _download_progress_hook(self, d):
        if d['status'] == 'downloading':
            if self.pbar is None:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                self.pbar = tqdm(
                    total=total,
                    unit='iB',
                    unit_scale=True,
                    desc="Downloading audio"
                )
            downloaded = d.get('downloaded_bytes', 0)
            self.pbar.update(downloaded - self.pbar.n)
        elif d['status'] == 'finished':
            if self.pbar:
                self.pbar.close()
                self.pbar = None

    def download_audio(self, url, output_path):
        """Download audio from YouTube video."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Modify options to include the output path
            opts = dict(self.ydl_opts)
            opts['outtmpl'] = output_path
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Download the file
                ydl.download([url])
                
                # The file should exist with .mp3 extension due to the postprocessor
                if os.path.exists(output_path):
                    return output_path
                # If not found, try with .mp3 extension
                mp3_path = f"{os.path.splitext(output_path)[0]}.mp3"
                if os.path.exists(mp3_path):
                    return mp3_path
                raise FileNotFoundError(f"Could not find downloaded audio file at {output_path} or {mp3_path}")
                
        except Exception as e:
            print(f"Error downloading audio: {str(e)}")
            raise
        finally:
            if self.pbar:
                self.pbar.close()
                self.pbar = None

    def get_whisper_transcript(self, url):
        """Get transcript using Whisper."""
        self._load_model()  # Load model only when needed
        
        self.cancelled = False
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp_audio_files")
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_audio = os.path.join(temp_dir, "temp_audio")
        actual_file = None
        
        # Store original signal handler
        original_handler = signal.getsignal(signal.SIGINT)
        
        try:
            actual_file = self.download_audio(url, temp_audio)
            if not os.path.exists(actual_file):
                raise FileNotFoundError(f"Downloaded audio file not found: {actual_file}")
                
            print(f"\nTranscribing audio file: {actual_file}")
            
            # Initialize variables for progress tracking
            start_time = time.time()
            last_progress = 0
            processing_rate = None
            eta = None
            
            def signal_handler(signum, frame):
                self.cancelled = True
                # Restore original handler for subsequent Ctrl+C
                signal.signal(signal.SIGINT, original_handler)
                print("\nCancelling Whisper transcription...")
            
            # Set up signal handler
            signal.signal(signal.SIGINT, signal_handler)
            
            with tqdm(total=100, desc="Transcribing", unit="%", bar_format='{l_bar}{bar}| {n:.0f}%{postfix}') as pbar:
                def progress_callback(progress):
                    if self.cancelled:
                        raise KeyboardInterrupt("Whisper transcription cancelled")
                    
                    nonlocal last_progress, processing_rate, eta, start_time
                    
                    current_time = time.time()
                    elapsed = current_time - start_time
                    progress_percent = int(progress * 100)
                    
                    # Calculate processing rate after 5% progress
                    if progress > 0.05 and processing_rate is None:
                        processing_rate = elapsed / progress
                        estimated_total = processing_rate
                        eta = start_time + estimated_total
                        
                    # Update ETA continuously after initial estimate
                    if processing_rate is not None:
                        remaining_time = (eta - current_time) if eta else None
                        if remaining_time:
                            eta_str = str(timedelta(seconds=int(remaining_time)))
                            rate = f"{progress_percent/elapsed:.1f}%/s"
                            pbar.set_postfix_str(f"ETA: {eta_str}, Rate: {rate}")
                    
                    # Update progress bar
                    update_size = progress_percent - last_progress
                    if update_size > 0:
                        pbar.update(update_size)
                        last_progress = progress_percent
                
                result = self.model.transcribe(
                    actual_file,
                    progress_callback=progress_callback
                )
            
            return result
            
        except KeyboardInterrupt:
            print("\nWhisper transcription cancelled")
            return None
        except Exception as e:
            print(f"Error in get_whisper_transcript: {str(e)}")
            return None
        finally:
            # Restore original signal handler
            signal.signal(signal.SIGINT, original_handler)
            # Cleanup
            try:
                if actual_file and os.path.exists(actual_file):
                    os.remove(actual_file)
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                print(f"Error during cleanup: {str(e)}") 