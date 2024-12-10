import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

class YouTubeExtractor:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

    def extract_video_id(self, url):
        """Extract video ID from URL."""
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info['id']

    def extract_metadata(self, url):
        """Extract title, description, and top comments."""
        with yt_dlp.YoutubeDL({
            **self.ydl_opts,
            'getcomments': True,
            'extract_flat': False,
        }) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Get top 5 liked comments
            comments = info.get('comments', [])
            top_comments = sorted(
                comments,
                key=lambda x: x.get('like_count', 0),
                reverse=True
            )[:5]

            return {
                'title': info['title'],
                'description': info['description'],
                'top_comments': top_comments
            }

    def get_auto_transcript(self, video_id):
        """Get auto-generated transcript."""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return transcript
        except Exception as e:
            print(f"Error getting auto-generated transcript: {e}")
            return None 