import os
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

FONT_PATHS = {
    'chinese': os.path.join(BASE_DIR, 'wqy-MicroHei.ttf'),
    'noto': os.path.join(BASE_DIR, 'Noto_Sans', 'static', 'NotoSans-Regular.ttf'),
}

PLOTS_DIR = 'plots'

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

CHINESE_STOPWORDS_FILE = os.path.join(BASE_DIR, 'chinese_stopwords.txt')
