from src.main import YouTubeAnalyzer

if __name__ == "__main__":
    analyzer = YouTubeAnalyzer()
    url = input("Enter YouTube URL: ")
    viewer_profile = input("Enter viewer profile (or press Enter for default): ").strip()
    
    analyzer.analyze_video(url, viewer_profile if viewer_profile else None) 