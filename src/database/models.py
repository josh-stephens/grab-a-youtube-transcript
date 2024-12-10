from sqlalchemy import create_engine, Column, String, DateTime, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from pathlib import Path

# Create the database directory if it doesn't exist
db_dir = Path(__file__).parent.parent.parent / 'data'
db_dir.mkdir(exist_ok=True)

# Create database engine
DATABASE_URL = f"sqlite:///{db_dir}/videos.db"
engine = create_engine(DATABASE_URL)

# Create declarative base
Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'

    id = Column(String, primary_key=True)  # YouTube video ID
    url = Column(String, nullable=False)
    title = Column(String)
    description = Column(String)
    processed_at = Column(DateTime, default=datetime.utcnow)
    top_comments = Column(JSON)  # Store as JSON
    transcript_file = Column(String)  # Path to transcript file
    analysis_file = Column(String)   # Path to analysis file
    info_quality_score = Column(Integer)
    viewer_interest_score = Column(Integer)

# Create all tables
Base.metadata.create_all(engine)

# Create session factory
Session = sessionmaker(bind=engine) 