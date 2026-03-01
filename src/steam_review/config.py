import os
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

FONT_PATHS = {
    'chinese': os.path.join(PROJECT_ROOT, 'data', 'wqy-MicroHei.ttf'),
    'noto': os.path.join(PROJECT_ROOT, 'Noto_Sans', 'static', 'NotoSans-Regular.ttf'),
}

DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'reviews.db')

PLOTS_DIR = 'plots'

# Game name mapping (App ID -> Game Name)
GAME_NAMES = {
    '2897760': 'Romantic Escapades',
    '2277560': 'WUCHANG: Fallen Feathers',
    '3363270': "Fischer's Fishing Journey",
}

def get_game_name(app_id):
    """Get game name from App ID"""
    if app_id is None:
        return "Unknown"
    return GAME_NAMES.get(str(app_id), f"App {app_id}")

SCRAPER_CONFIG = {
    'max_concurrent_requests': 5,
    'default_timeout': 10,
    'max_retries': 5,
    'backoff_factor': 1,
}

ANALYSIS_CONFIG = {
    'language_batch_size': 1000,
    'playtime_bins': [0, 1, 5, 10, 20, 50, 100, 200, 500],
    'playtime_labels': ['<1h', '1-5h', '5-10h', '10-20h', '20-50h', '50-100h', '100-200h', '200-500h'],
    'review_length_bins': [0, 50, 100, 200, 500, 1000, float('inf')],
    'review_length_labels': ['<50', '50-100', '100-200', '200-500', '500-1000', '>1000'],
}

CHINESE_STOPWORDS_FILE = os.path.join(PROJECT_ROOT, 'data', 'chinese_stopwords.txt')
