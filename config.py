import os
from dotenv import load_dotenv
from pathlib import Path
import torch

load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_DIR = PROJECT_ROOT / 'output'

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Default settings
DEFAULT_VIEWER_PROFILE = "the average humanist/idealist AI technology and enthusiast"

# Whisper settings
WHISPER_MODEL = "large-v3"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Output settings
OUTPUT_DIR = "output"

# Add to existing config.py
MAX_TOKENS_THRESHOLD = 1000  # Adjust this value as needed 