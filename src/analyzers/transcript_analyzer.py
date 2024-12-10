import os
from openai import OpenAI
import sys
from pathlib import Path
import json

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import OPENAI_API_KEY

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Use GPT-4 Turbo with appropriate token limits
MODEL = "gpt-4-1106-preview"
TEMPERATURE = 0.7

class TranscriptAnalyzer:
    def compare_transcripts(self, auto_transcript, whisper_transcript):
        """Compare and synthesize transcripts using AI."""
        # Prepare transcripts for comparison
        auto_text = self._format_transcript(auto_transcript)
        whisper_text = whisper_transcript['text'] if whisper_transcript else None

        system_prompt = """You are a transcript editor. Your task is to:
        1. Create an accurate, corrected version of the transcript
        2. Provide a detailed report of changes made
        3. Format your response as follows:
           # Corrected Transcript
           [Your corrected transcript here]
           
           # Changes Made
           [Your detailed report here]"""

        if whisper_text:
            user_prompt = f"""Compare and correct these two transcripts:

            Auto-generated transcript:
            {auto_text}

            Whisper transcript:
            {whisper_text}

            In your report, include:
            1. Major corrections made
            2. How the Whisper transcript helped improve accuracy
            3. Any significant discrepancies between the versions
            4. Confidence assessment of the final version"""
        else:
            user_prompt = f"""Review and correct this transcript:

            {auto_text}

            In your report, include:
            1. Major corrections made
            2. Common transcription errors fixed
            3. Confidence assessment of the final version"""

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=TEMPERATURE
            )
            
            return {
                'text': response.choices[0].message.content,
                'whisper_used': bool(whisper_text)
            }
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            raise

    def analyze_content(self, metadata, corrected_transcript, viewer_profile):
        """Analyze video content and generate insights."""
        system_prompt = f"""You are analyzing video content for {viewer_profile}.
        Format your response as JSON with the following structure:
        {{
            "salient_points": [list of key points],
            "counterfactuals": [list of alternative viewpoints],
            "bias": "assessment of bias",
            "claims_to_review": [list of claims],
            "info_quality": score (1-10),
            "viewer_interest": score (1-10)
        }}"""

        user_prompt = f"""Analyze this video content:

        Title: {metadata['title']}
        Description: {metadata['description']}
        Transcript: {corrected_transcript}"""

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            analysis = json.loads(response.choices[0].message.content)
            return analysis

        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            raise

    def _format_transcript(self, transcript):
        """Format transcript for comparison."""
        return " ".join([entry['text'] for entry in transcript]) 