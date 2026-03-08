import pytest
import pandas as pd
import sqlite3
import os
from unittest.mock import patch, MagicMock


class TestDatabase:
    @pytest.fixture
    def temp_db(self, tmp_path):
        db_path = tmp_path / "test_reviews.db"
        from src.steam_review.storage.database import ReviewDatabase
        db = ReviewDatabase(db_path=str(db_path))
        yield db
        if os.path.exists(db_path):
            os.remove(db_path)

    def test_database_initialization(self, temp_db):
        assert os.path.exists(temp_db.db_path)
        conn = sqlite3.connect(temp_db.db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reviews'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_insert_reviews_empty_dataframe(self, temp_db):
        df = pd.DataFrame()
        result = temp_db.insert_reviews(df)
        assert result == 0

    def test_insert_reviews_with_data(self, temp_db):
        df = pd.DataFrame({
            'recommendation_id': ['1', '2', '3'],
            'app_id': ['123', '123', '123'],
            'language': ['en', 'en', 'zh'],
            'review': ['Good game', 'Bad game', '好游戏'],
            'voted_up': [True, False, True]
        })
        result = temp_db.insert_reviews(df)
        assert result == 3

    def test_insert_reviews_duplicate(self, temp_db):
        df = pd.DataFrame({
            'recommendation_id': ['1', '2'],
            'app_id': ['123', '123'],
            'language': ['en', 'en'],
            'review': ['Good', 'Bad'],
            'voted_up': [True, False]
        })
        temp_db.insert_reviews(df)
        
        df_duplicate = pd.DataFrame({
            'recommendation_id': ['1', '3'],
            'app_id': ['123', '123'],
            'language': ['en', 'en'],
            'review': ['Good', 'New'],
            'voted_up': [True, True]
        })
        result = temp_db.insert_reviews(df_duplicate)
        assert result == 1

    def test_get_existing_ids(self, temp_db):
        df = pd.DataFrame({
            'recommendation_id': ['1', '2', '3'],
            'app_id': ['123', '123', '123'],
            'language': ['en', 'en', 'en'],
            'review': ['a', 'b', 'c'],
            'voted_up': [True, True, True]
        })
        temp_db.insert_reviews(df)
        
        existing_ids = temp_db.get_existing_ids()
        assert existing_ids == {'1', '2', '3'}

    def test_get_stats(self, temp_db):
        df = pd.DataFrame({
            'recommendation_id': ['1', '2', '3', '4'],
            'app_id': ['123', '123', '123', '456'],
            'language': ['en', 'en', 'en', 'en'],
            'review': ['a', 'b', 'c', 'd'],
            'voted_up': [True, True, False, True]
        })
        temp_db.insert_reviews(df)
        
        stats = temp_db.get_stats('123')
        assert stats['total'] == 3
        assert stats['positive'] == 2
        assert stats['negative'] == 1


class TestConfig:
    def test_project_root_path(self):
        from src.steam_review import config
        assert config.PROJECT_ROOT is not None
        assert config.BASE_DIR.name == 'steam_review'

    def test_font_paths_exist(self):
        from src.steam_review import config
        assert 'chinese' in config.FONT_PATHS
        assert 'noto' in config.FONT_PATHS

    def test_get_game_name(self):
        from src.steam_review import config
        assert config.get_game_name('2277560') == 'WUCHANG: Fallen Feathers'
        assert config.get_game_name('999999') == 'App 999999'
        assert config.get_game_name(None) == 'Unknown'

    def test_scraper_config(self):
        from src.steam_review import config
        assert config.SCRAPER_CONFIG['max_concurrent_requests'] == 5
        assert config.SCRAPER_CONFIG['default_timeout'] == 10

    def test_analysis_config(self):
        from src.steam_review import config
        assert len(config.ANALYSIS_CONFIG['playtime_bins']) == 9
        assert len(config.ANALYSIS_CONFIG['playtime_labels']) == 8
