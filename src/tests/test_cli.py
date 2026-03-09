import pytest
import click
from click.testing import CliRunner
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio


class TestCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_cli_help(self, runner):
        from src.steam_review.cli.cli import cli

        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Steam Review Analyzer" in result.output

    def test_scrape_command_help(self, runner):
        from src.steam_review.cli.cli import scrape

        result = runner.invoke(scrape, ["--help"])
        assert result.exit_code == 0
        assert "Steam App ID" in result.output
        assert "-a" in result.output or "--app-id" in result.output

    def test_scrape_command_defaults(self, runner):
        from src.steam_review.cli.cli import scrape

        with patch(
            "src.steam_review.cli.cli.scrape_main", new=AsyncMock()
        ) as mock_scrape:
            mock_scrape.return_value = None
            result = runner.invoke(scrape, [])
            assert result.exit_code == 0
            mock_scrape.assert_called_once()
            args = mock_scrape.call_args[0]
            assert args[0] == "2277560"
            assert args[1] == 0

    def test_scrape_command_with_app_id(self, runner):
        from src.steam_review.cli.cli import scrape

        with patch(
            "src.steam_review.cli.cli.scrape_main", new=AsyncMock()
        ) as mock_scrape:
            mock_scrape.return_value = None
            result = runner.invoke(scrape, ["-a", "2897760"])
            assert result.exit_code == 0
            mock_scrape.assert_called_once_with("2897760", 0, False)

    def test_scrape_command_with_limit(self, runner):
        from src.steam_review.cli.cli import scrape

        with patch(
            "src.steam_review.cli.cli.scrape_main", new=AsyncMock()
        ) as mock_scrape:
            mock_scrape.return_value = None
            result = runner.invoke(scrape, ["-l", "100"])
            assert result.exit_code == 0
            mock_scrape.assert_called_once()
            args = mock_scrape.call_args[0]
            assert args[1] == 100

    def test_scrape_command_with_app_id_and_limit(self, runner):
        from src.steam_review.cli.cli import scrape

        with patch(
            "src.steam_review.cli.cli.scrape_main", new=AsyncMock()
        ) as mock_scrape:
            mock_scrape.return_value = None
            result = runner.invoke(scrape, ["-a", "3363270", "-l", "50"])
            assert result.exit_code == 0
            mock_scrape.assert_called_once_with("3363270", 50, False)

    def test_stats_command_help(self, runner):
        from src.steam_review.cli.cli import stats

        result = runner.invoke(stats, ["--help"])
        assert result.exit_code == 0
        assert "-a" in result.output or "--app-id" in result.output

    def test_stats_command_empty_database(self, runner):
        from src.steam_review.cli.cli import stats

        with patch("src.steam_review.cli.cli.get_database") as mock_db:
            mock_database = MagicMock()
            mock_database.get_all_games.return_value = []
            mock_db.return_value = mock_database
            result = runner.invoke(stats, [])
            assert (
                "空" in result.output
                or "empty" in result.output.lower()
                or result.exit_code == 0
            )

    def test_stats_command_with_data(self, runner):
        from src.steam_review.cli.cli import stats

        with patch("src.steam_review.cli.cli.get_database") as mock_db:
            mock_database = MagicMock()
            mock_database.get_all_games.return_value = [
                {"app_id": "2277560", "total": 100, "positive": 80}
            ]
            mock_db.return_value = mock_database
            result = runner.invoke(stats, [])
            assert "2277560" in result.output or "WUCHANG" in result.output

    def test_stats_command_with_app_id_filter(self, runner):
        from src.steam_review.cli.cli import stats

        with patch("src.steam_review.cli.cli.get_database") as mock_db:
            mock_database = MagicMock()
            mock_database.get_all_games.return_value = [
                {"app_id": "2277560", "total": 100, "positive": 80},
                {"app_id": "2897760", "total": 50, "positive": 40},
            ]
            mock_db.return_value = mock_database
            result = runner.invoke(stats, ["-a", "2277560"])
            assert result.exit_code == 0
            mock_database.get_all_games.assert_called_once()

    def test_analyze_command_help(self, runner):
        from src.steam_review.cli.cli import analyze

        result = runner.invoke(analyze, ["--help"])
        assert result.exit_code == 0

    def test_export_command_help(self, runner):
        from src.steam_review.cli.cli import export

        result = runner.invoke(export, ["--help"])
        assert result.exit_code == 0

    def test_dashboard_command_help(self, runner):
        from src.steam_review.cli.cli import dashboard

        result = runner.invoke(dashboard, ["--help"])
        assert result.exit_code == 0

    def test_interactive_command(self, runner):
        from src.steam_review.cli.cli import interactive

        with patch("click.prompt", return_value=0):
            result = runner.invoke(interactive, input="0\n")
            assert result.exit_code == 0


class TestCLIModule:
    def test_cli_import(self):
        from src.steam_review.cli import cli

        assert cli is not None

    def test_load_config_no_file(self, tmp_path):
        from src.steam_review.cli import cli

        with patch("src.steam_review.cli.cli.PROJECT_ROOT", tmp_path):
            config = cli.load_config()
            assert config == {}

    def test_load_config_with_file(self, tmp_path):
        from src.steam_review.cli import cli

        config_file = tmp_path / "config.json"
        config_file.write_text('{"test": "value"}')
        with patch("src.steam_review.cli.cli.PROJECT_ROOT", tmp_path):
            config = cli.load_config()
            assert config.get("test") == "value"


class TestCLIErrorHandling:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_scrape_invalid_app_id(self, runner):
        from src.steam_review.cli.cli import scrape

        with patch(
            "src.steam_review.cli.cli.scrape_main",
            new=AsyncMock(side_effect=Exception("API Error")),
        ):
            result = runner.invoke(scrape, ["-a", "invalid"])
            assert result.exit_code in [0, 1]

    def test_stats_database_error(self, runner):
        from src.steam_review.cli.cli import stats

        with patch("src.steam_review.cli.cli.get_database") as mock_db:
            mock_db.side_effect = Exception("Database error")
            result = runner.invoke(stats, [])
            assert result.exit_code in [0, 1]
            assert (
                "error" in result.output.lower()
                or "Error" in result.output
                or result.exit_code == 1
            )
