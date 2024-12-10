from .models import Session, Video
from datetime import datetime
from pathlib import Path

class DatabaseHandler:
    def __init__(self):
        self.session = Session()

    def add_video(self, video_data):
        """Add or update video entry in database."""
        try:
            video = Video(
                id=video_data['video_id'],
                url=video_data['url'],
                title=video_data['metadata']['title'],
                description=video_data['metadata']['description'],
                top_comments=video_data['metadata']['top_comments'],
                transcript_file=video_data['transcript_file'],
                analysis_file=video_data['analysis_file'],
                info_quality_score=video_data.get('info_quality_score'),
                viewer_interest_score=video_data.get('viewer_interest_score'),
                processed_at=datetime.utcnow()
            )
            
            existing = self.session.query(Video).filter_by(id=video.id).first()
            if existing:
                # Update existing entry
                for key, value in video_data.items():
                    setattr(existing, key, value)
            else:
                # Add new entry
                self.session.add(video)
                
            self.session.commit()
            return video
            
        except Exception as e:
            self.session.rollback()
            raise e

    def get_video(self, video_id):
        """Retrieve video entry from database."""
        return self.session.query(Video).filter_by(id=video_id).first()

    def video_exists(self, video_id):
        """Check if video has been processed before."""
        return self.session.query(Video).filter_by(id=video_id).count() > 0

    def close(self):
        """Close the database session."""
        self.session.close() 