import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open


class TestConfig:
    def test_project_root_path(self):
        from src.steam_review import config

        assert config.PROJECT_ROOT is not None
        assert config.BASE_DIR.name == "steam_review"

    def test_font_paths_exist(self):
        from src.steam_review import config

        assert "chinese" in config.FONT_PATHS
        assert "noto" in config.FONT_PATHS

    def test_get_game_name_known_app(self):
        from src.steam_review import config

        assert config.get_game_name("2277560") == "WUCHANG: Fallen Feathers"
        assert config.get_game_name("2897760") == "Romantic Escapades"

    def test_get_game_name_unknown_app(self):
        from src.steam_review import config

        assert config.get_game_name("999999") == "App 999999"
        assert config.get_game_name("12345") == "App 12345"

    def test_get_game_name_none(self):
        from src.steam_review import config

        assert config.get_game_name(None) == "Unknown"

    def test_get_game_name_string_conversion(self):
        from src.steam_review import config

        assert config.get_game_name(2277560) == "WUCHANG: Fallen Feathers"

    def test_scraper_config(self):
        from src.steam_review import config

        assert config.SCRAPER_CONFIG["max_concurrent_requests"] == 5
        assert config.SCRAPER_CONFIG["default_timeout"] == 10
        assert config.SCRAPER_CONFIG["max_retries"] == 5

    def test_analysis_config(self):
        from src.steam_review import config

        assert len(config.ANALYSIS_CONFIG["playtime_bins"]) == 9
        assert len(config.ANALYSIS_CONFIG["playtime_labels"]) == 8
        assert len(config.ANALYSIS_CONFIG["review_length_bins"]) == 7
        assert len(config.ANALYSIS_CONFIG["review_length_labels"]) == 6

    def test_db_path(self):
        from src.steam_review import config

        assert "reviews.db" in config.DB_PATH
        assert "data" in config.DB_PATH

    def test_plots_dir(self):
        from src.steam_review import config

        assert config.PLOTS_DIR == "plots"

    def test_chinese_stopwords_file(self):
        from src.steam_review import config

        assert "chinese_stopwords.txt" in config.CHINESE_STOPWORDS_FILE

    def test_ensure_project_path(self):
        from src.steam_review import config
        import sys

        original_path = sys.path.copy()
        config.ensure_project_path()
        assert str(config.PROJECT_ROOT) in sys.path
        sys.path = original_path


class TestConfigFileLoading:
    @pytest.fixture
    def temp_config_file(self, tmp_path):
        config_file = tmp_path / "config.json"
        test_config = {"game_names": {"111111": "Test Game", "222222": "Another Game"}}
        config_file.write_text(json.dumps(test_config), encoding="utf-8")
        return config_file

    def test_load_game_names_from_config_file(self, temp_config_file):
        from src.steam_review import config

        with patch.object(config, "CONFIG_FILE", temp_config_file):
            result = config._load_game_names_from_config()
            assert result == {"111111": "Test Game", "222222": "Another Game"}

    def test_load_game_names_nonexistent_file(self, tmp_path):
        from src.steam_review import config

        non_existent = tmp_path / "nonexistent.json"
        with patch.object(config, "CONFIG_FILE", non_existent):
            result = config._load_game_names_from_config()
            assert result == {}

    def test_load_game_names_invalid_json(self, tmp_path):
        from src.steam_review import config

        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json", encoding="utf-8")
        with patch.object(config, "CONFIG_FILE", invalid_file):
            result = config._load_game_names_from_config()
            assert result == {}

    def test_merge_game_names(self):
        from src.steam_review import config

        with patch.object(
            config,
            "_load_game_names_from_config",
            return_value={"333333": "Merged Game"},
        ):
            result = config._merge_game_names()
            assert "2277560" in result
            assert "333333" in result
            assert result["2277560"] == "WUCHANG: Fallen Feathers"

    def test_config_file_game_names_override_defaults(self, tmp_path):
        from src.steam_review import config

        config_file = tmp_path / "config.json"
        override_config = {"game_names": {"2277560": "Overridden Name"}}
        config_file.write_text(json.dumps(override_config), encoding="utf-8")
        with patch.object(config, "CONFIG_FILE", config_file):
            names = config._merge_game_names()
            assert names["2277560"] == "Overridden Name"
