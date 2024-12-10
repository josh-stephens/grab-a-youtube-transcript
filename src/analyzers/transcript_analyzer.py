import os
from openai import OpenAI
import sys
from pathlib import Path
import json
import tiktoken
import time
from datetime import datetime, timedelta

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import OPENAI_API_KEY, MAX_TOKENS_THRESHOLD

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Use GPT-4 Turbo for text analysis
MODEL = "gpt-4-1106-preview"
TEMPERATURE = 0.7

class TranscriptAnalyzer:
    def __init__(self):
        self.encoding = tiktoken.encoding_for_model(MODEL)

    def _format_time(self, seconds):
        """Format seconds into human readable time."""
        return str(timedelta(seconds=int(seconds)))

    def _time_operation(self, operation, *args, **kwargs):
        """Time an operation and return its result with timing info."""
        start_time = time.time()
        result = operation(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"\nOperation completed in: {self._format_time(elapsed)}")
        return result

    def compare_transcripts(self, auto_transcript, whisper_transcript):
        """Compare and synthesize transcripts using AI."""
        print("\nStarting transcript comparison...")
        
        # Format transcripts
        auto_text = self._format_transcript(auto_transcript)
        whisper_text = whisper_transcript['text'] if whisper_transcript else None

        # Optimize prompts for efficiency
        system_prompt = """You are a transcript editor. Create a corrected transcript and change report in this format:
        # Corrected Transcript
        [transcript]
        # Changes Made
        [changes]"""

        user_prompt = f"""Compare and correct:
        Auto: {auto_text}
        {'Whisper: ' + whisper_text if whisper_text else ''}"""

        # Token counting and approval
        total_tokens = self.count_tokens(system_prompt) + self.count_tokens(user_prompt)
        print(f"\nEstimated token count: {total_tokens}")
        
        if not self._confirm_token_usage(total_tokens):
            return None

        try:
            def api_call():
                return client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=MODEL,
                    temperature=TEMPERATURE
                )

            completion = self._time_operation(api_call)
            actual_tokens = completion.usage.total_tokens
            print(f"Actual tokens used: {actual_tokens}")
            
            return {
                'text': completion.choices[0].message.content,
                'whisper_used': bool(whisper_text),
                'tokens_used': actual_tokens
            }

        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            raise

    def analyze_content(self, metadata, corrected_transcript, viewer_profile):
        """Analyze video content and generate insights."""
        print("\nStarting content analysis...")

        # Optimize prompts for efficiency
        system_prompt = """Analyze content and return JSON with: salient_points[], counterfactuals[], bias, claims_to_review[], info_quality(1-10), viewer_interest(1-10)"""
        
        user_prompt = f"""Title: {metadata['title']}
        Description: {metadata['description']}
        Profile: {viewer_profile}
        Transcript: {corrected_transcript}"""

        # Token counting and approval
        total_tokens = self.count_tokens(system_prompt) + self.count_tokens(user_prompt)
        print(f"\nEstimated token count: {total_tokens}")
        
        if not self._confirm_token_usage(total_tokens):
            return None

        try:
            def api_call():
                return client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=MODEL,
                    temperature=TEMPERATURE,
                    response_format={"type": "json_object"}
                )

            completion = self._time_operation(api_call)
            actual_tokens = completion.usage.total_tokens
            print(f"Actual tokens used: {actual_tokens}")

            # Parse and validate JSON response
            try:
                analysis = json.loads(completion.choices[0].message.content)
                # Ensure numeric scores
                analysis['info_quality'] = int(analysis['info_quality'])
                analysis['viewer_interest'] = int(analysis['viewer_interest'])
                return analysis
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing response: {str(e)}")
                raise

        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            raise

    def _format_transcript(self, transcript):
        """Format transcript for comparison."""
        return " ".join(str(entry['text']) for entry in transcript)

    def count_tokens(self, text):
        """Count tokens in text using the model's tokenizer."""
        return len(self.encoding.encode(str(text)))

    def _confirm_token_usage(self, token_count):
        """Ask for user confirmation if token count is high."""
        if token_count > MAX_TOKENS_THRESHOLD:
            response = input(f"\nThis will use approximately {token_count} tokens. Continue? (y/N): ")
            return response.lower() == 'y'
        return True