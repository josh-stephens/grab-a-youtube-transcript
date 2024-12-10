class MarkdownFormatter:
    def format_transcript(self, transcript_data, timestamps=True):
        """Format transcript and processing report in Markdown."""
        md_lines = ["# Transcript Analysis\n\n"]
        
        # Add transcription processing information
        md_lines.append("## Processing Information\n")
        if transcript_data['whisper_used']:
            md_lines.append("This transcript was processed using both YouTube's auto-generated transcript and Whisper AI transcription.\n")
        else:
            md_lines.append("This transcript was processed using YouTube's auto-generated transcript only.\n")

        # Split the transcript text into sections
        content = transcript_data['text']
        sections = content.split("# ")
        
        # Process each section
        for section in sections:
            if section.strip():
                # Add the section header back and the content
                md_lines.append(f"## {section}")
                
        return "".join(md_lines)

    def format_analysis(self, analysis_results):
        """Format analysis results in Markdown."""
        return f"""# Video Analysis

## Salient Points
{self._format_list(analysis_results['salient_points'])}

## Counterfactual Viewpoints
{self._format_list(analysis_results['counterfactuals'])}

## Bias Assessment
{analysis_results['bias']}

## Claims to Review
{self._format_list(analysis_results['claims_to_review'])}

## Scores
- Information Quality: {analysis_results['info_quality']}/10
- Viewer Interest: {analysis_results['viewer_interest']}/10
"""

    def _format_list(self, items):
        """Format a list of items as markdown bullet points."""
        if not items:
            return "None provided"
        return "\n".join(f"- {item}" for item in items)

    def _format_timestamp(self, seconds):
        """Convert seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}" 