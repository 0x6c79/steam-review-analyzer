import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent.parent

CONFIG_FILE = PROJECT_ROOT / "config.json"


def _load_game_names_from_config() -> Dict[str, str]:
    """Load game names from config file if exists"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config_data: Dict[str, str] = {}
                raw = json.load(f)
                game_names = raw.get("game_names", {})
                if isinstance(game_names, dict):
                    config_data = game_names
                return config_data
        except Exception:
            pass
    return {}


def _get_default_game_names() -> Dict[str, str]:
    """Get default game names"""
    return {
        "2897760": "Romantic Escapades",
        "2277560": "WUCHANG: Fallen Feathers",
        "3363270": "Fischer's Fishing Journey",
    }


def ensure_project_path():
    """Ensure project root is in sys.path for imports"""
    import sys

    project_str = str(PROJECT_ROOT)
    if project_str not in sys.path:
        sys.path.insert(0, project_str)


def setup_logging(level=logging.INFO):
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


FONT_PATHS = {
    "chinese": os.path.join(PROJECT_ROOT, "data", "wqy-MicroHei.ttf"),
    "noto": os.path.join(PROJECT_ROOT, "Noto_Sans", "static", "NotoSans-Regular.ttf"),
}

DB_PATH = os.path.join(PROJECT_ROOT, "data", "reviews.db")

PLOTS_DIR = "plots"

# Game name mapping (App ID -> Game Name)
# Priority: config file > environment variable > default
_GameNamesType = Optional[Dict[str, str]]


def _merge_game_names() -> Dict[str, str]:
    """Merge game names from multiple sources"""
    defaults = _get_default_game_names()
    config_names = _load_game_names_from_config()
    defaults.update(config_names)
    return defaults


GAME_NAMES: Dict[str, str] = _merge_game_names()


def get_game_name(app_id):
    """Get game name from App ID"""
    if app_id is None:
        return "Unknown"
    return GAME_NAMES.get(str(app_id), f"App {app_id}")


SCRAPER_CONFIG = {
    "max_concurrent_requests": 5,
    "default_timeout": 10,
    "max_retries": 5,
    "backoff_factor": 1,
}

ANALYSIS_CONFIG = {
    "language_batch_size": 1000,
    "playtime_bins": [0, 1, 5, 10, 20, 50, 100, 200, 500],
    "playtime_labels": [
        "<1h",
        "1-5h",
        "5-10h",
        "10-20h",
        "20-50h",
        "50-100h",
        "100-200h",
        "200-500h",
    ],
    "review_length_bins": [0, 50, 100, 200, 500, 1000, float("inf")],
    "review_length_labels": [
        "<50",
        "50-100",
        "100-200",
        "200-500",
        "500-1000",
        ">1000",
    ],
}

CHINESE_STOPWORDS_FILE = os.path.join(PROJECT_ROOT, "data", "chinese_stopwords.txt")
