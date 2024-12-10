import os
import sys
from pathlib import Path
from tqdm import tqdm
import time
from datetime import datetime, timedelta
import signal
import whisperx
import torch

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import WHISPER_MODEL, DEVICE

class WhisperExtractor:
    def __init__(self):
        self.model = None
        self.diarize_model = None
        self._whisperx = None  # Add this to lazy load the entire module
        self._torch = None
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self._download_progress_hook],
        }
        self.pbar = None
        self.cancelled = False

    def _load_dependencies(self):
        """Lazy load all required modules only when needed"""
        if self._whisperx is None:
            print("\nLoading WhisperX dependencies...")
            import whisperx
            import torch
            self._whisperx = whisperx
            self._torch = torch

    def _load_models(self):
        """Lazy load the WhisperX models when needed."""
        if self.model is None:
            self._load_dependencies()
            print("\nLoading WhisperX models...")
            try:
                self.model = self._whisperx.load_model(
                    WHISPER_MODEL,
                    device=DEVICE,
                    compute_type="float16"
                )
                
                self.diarize_model = self._whisperx.DiarizationPipeline(
                    use_auth_token=None,
                    device=DEVICE
                )
            except Exception as e:
                print(f"Error loading models: {str(e)}")
                raise

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
        """Get transcript using WhisperX."""
        self._load_models()
        
        self.cancelled = False
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp_audio_files")
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_audio = os.path.join(temp_dir, "temp_audio")
        actual_file = None
        
        original_handler = signal.getsignal(signal.SIGINT)
        
        try:
            actual_file = self.download_audio(url, temp_audio)
            if not os.path.exists(actual_file):
                raise FileNotFoundError(f"Downloaded audio file not found: {actual_file}")
                
            print(f"\nTranscribing audio file: {actual_file}")
            
            def signal_handler(signum, frame):
                self.cancelled = True
                signal.signal(signal.SIGINT, original_handler)
                print("\nCancelling WhisperX transcription...")
            
            signal.signal(signal.SIGINT, signal_handler)
            
            with tqdm(total=4, desc="Processing", unit="step") as pbar:
                # Transcribe with original whisper model
                result = self.model.transcribe(actual_file, batch_size=16)
                pbar.update(1)
                
                if self.cancelled:
                    raise KeyboardInterrupt("WhisperX transcription cancelled")

                # Align whisper output
                result = whisperx.align(
                    result["segments"],
                    self.model,
                    actual_file,
                    DEVICE,
                    return_char_alignments=False
                )
                pbar.update(1)
                
                if self.cancelled:
                    raise KeyboardInterrupt("WhisperX transcription cancelled")

                # Get speaker diarization
                diarize_segments = self.diarize_model(actual_file)
                pbar.update(1)
                
                if self.cancelled:
                    raise KeyboardInterrupt("WhisperX transcription cancelled")

                # Assign speaker labels
                result = whisperx.assign_word_speakers(
                    diarize_segments,
                    result
                )
                pbar.update(1)

                # Format the result
                segments = []
                for segment in result["segments"]:
                    segments.append({
                        'text': segment['text'],
                        'start': segment['start'],
                        'end': segment['end'],
                        'speaker': segment.get('speaker', 'Unknown')
                    })

                return {
                    'text': ' '.join(s['text'] for s in segments),
                    'segments': segments
                }
            
        except KeyboardInterrupt:
            print("\nWhisperX transcription cancelled")
            return None
        except Exception as e:
            print(f"Error in get_whisper_transcript: {str(e)}")
            return None
        finally:
            signal.signal(signal.SIGINT, original_handler)
            try:
                if actual_file and os.path.exists(actual_file):
                    os.remove(actual_file)
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                print(f"Error during cleanup: {str(e)}") 