"""
Steam Review Analyzer - User-Friendly CLI
提供交互式和简化命令两种模式
"""

import os
import sys
import asyncio
import click
import logging
import json
from pathlib import Path
from typing import NoReturn, Any

# Determine project root - works in both dev and installed modes
cli_path = Path(__file__).resolve()
# cli_path = src/steam_review/cli/cli.py
# Go up to project root
PROJECT_ROOT: Path = cli_path.parent.parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from src.steam_review import config
from src.steam_review.scraper.steam_review_scraper import main as scrape_main
from src.steam_review.storage.database import get_database
from src.steam_review.utils.exceptions import (
    SteamReviewError,
    ScraperError,
    DatabaseError,
    SteamAPIError,
)

config.setup_logging()
logger: logging.Logger = logging.getLogger(__name__)


def handle_error(error: Exception) -> NoReturn:
    """Handle errors gracefully and exit with appropriate code"""
    error_msg: str = str(error)

    if isinstance(error, SteamAPIError):
        click.echo(f"❌ API 错误: {error_msg}", err=True)
        if error.status_code == 429:
            click.echo("⏳ 请稍后再试 (Steam API 限流)", err=True)
        sys.exit(1)
    elif isinstance(error, ScraperError):
        click.echo(f"❌ 爬取错误: {error_msg}", err=True)
        sys.exit(1)
    elif isinstance(error, DatabaseError):
        click.echo(f"❌ 数据库错误: {error_msg}", err=True)
        sys.exit(1)
    elif isinstance(error, SteamReviewError):
        click.echo(f"❌ 错误: {error_msg}", err=True)
        sys.exit(1)
    else:
        click.echo(f"❌ 未知错误: {error_msg}", err=True)
        logger.exception("Unexpected error occurred")
        sys.exit(1)


def load_config() -> dict[str, Any]:
    """Load user configuration"""
    config_file: Path = PROJECT_ROOT / "config.json"
    if config_file.exists():
        with open(config_file) as f:
            data: Any = json.load(f)
            if isinstance(data, dict):
                return data
    return {}


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """🎮 Steam Review Analyzer - 简单的命令行工具

    直接运行命令或使用交互模式:
        steam-review          # 交互模式
        steam-review scrape   # 快速爬取
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
def interactive():
    """🎯 交互式模式 - 选择要执行的操作"""
    click.echo("\n🎮 Steam Review Analyzer\n")

    options = [
        ("1", "爬取新评论", "scrape"),
        ("2", "分析已有数据", "analyze"),
        ("3", "查看统计数据", "stats"),
        ("4", "导出数据", "export"),
        ("5", "启动仪表盘", "dashboard"),
        ("0", "退出", "exit"),
    ]

    for key, desc, _ in options:
        click.echo(f"  {key}. {desc}")

    choice = click.prompt("\n请选择操作", type=int, default=1)

    if choice == 1:
        interactive_scrape()
    elif choice == 2:
        interactive_analyze()
    elif choice == 3:
        interactive_stats()
    elif choice == 4:
        interactive_export()
    elif choice == 5:
        interactive_dashboard()
    else:
        click.echo("再见! 👋")


def interactive_scrape():
    """交互式爬取"""
    click.echo("\n📥 爬取评论\n")

    # 显示常用游戏
    games = [
        ("1", "WUCHANG: Fallen Feathers", "2277560"),
        ("2", "Romantic Escapades", "2897760"),
        ("3", "Fischer's Fishing Journey", "3363270"),
        ("4", "自定义 App ID", "custom"),
    ]

    for key, name, app_id in games:
        click.echo(f"  {key}. {name}")

    choice = click.prompt("\n选择游戏", type=int, default=1)

    if choice == 1:
        app_id = "2277560"
    elif choice == 2:
        app_id = "2897760"
    elif choice == 3:
        app_id = "3363270"
    else:
        app_id = click.prompt("输入 Steam App ID", type=str)

    limit = click.prompt("爬取评论数量 (0=全部)", type=int, default=0)

    click.echo(f"\n🚀 开始爬取 App ID: {app_id}")
    if limit > 0:
        click.echo(f"   限制: {limit} 条")

    asyncio.run(scrape_main(app_id, limit, False))
    click.echo("\n✅ 完成!")


def interactive_analyze():
    """交互式分析"""
    click.echo("\n📊 分析数据\n")

    csv_files = list(Path("data").glob("*_reviews.csv"))
    if not csv_files:
        csv_files = list(Path(".").glob("*_reviews.csv"))

    if not csv_files:
        click.echo("❌ 未找到 CSV 文件，请先爬取数据")
        return

    click.echo("可用文件:")
    for i, f in enumerate(csv_files, 1):
        size = f.stat().st_size / 1024 / 1024
        click.echo(f"  {i}. {f.name} ({size:.1f} MB)")

    choice = click.prompt("\n选择文件 (0=退出)", type=int, default=1)

    if choice == 0:
        return
    if choice > len(csv_files):
        choice = len(csv_files)

    csv_file = csv_files[choice - 1]
    click.echo(f"\n🔍 分析: {csv_file.name}")

    from src.steam_review.full_analysis import generate_full_analysis

    generate_full_analysis(str(csv_file), "plots")

    click.echo("\n✅ 分析完成! 图表保存在 plots/ 目录")


def interactive_stats():
    """交互式统计"""
    click.echo("\n📈 数据库统计\n")

    db = get_database()
    games = db.get_all_games()

    if not games:
        click.echo("❌ 数据库为空，请先爬取数据")
        return

    for game in games:
        app_id = game["app_id"] or "未知"
        total = game["total"]
        positive = game["positive"]
        rate = positive / total * 100 if total > 0 else 0

        name = config.get_game_name(app_id)

        bar = "█" * int(rate / 5) + "░" * (20 - int(rate / 5))

        click.echo(f"\n🎮 {name}")
        click.echo(f"   App ID: {app_id}")
        click.echo(f"   总评论: {total}")
        click.echo(f"   好评: {positive} ({rate:.1f}%)")
        click.echo(f"   [{bar}]")


def interactive_export():
    """交互式导出"""
    click.echo("\n💾 导出数据\n")

    formats = [
        ("1", "CSV", "csv"),
        ("2", "Excel", "excel"),
        ("3", "JSON", "json"),
    ]

    click.echo("导出格式:")
    for key, name, _ in formats:
        click.echo(f"  {key}. {name}")

    choice = click.prompt("\n选择格式", type=int, default=1)
    fmt = formats[choice - 1][2]

    db = get_database()
    games = db.get_all_games()

    if not games:
        click.echo("❌ 数据库为空")
        return

    click.echo("\n选择游戏:")
    click.echo("  0. 全部")
    for i, g in enumerate(games, 1):
        name = config.get_game_name(g["app_id"])
        click.echo(f"  {i}. {name} ({g['total']} 条)")

    choice = click.prompt("\n选择", type=int, default=0)
    app_id = games[choice - 1]["app_id"] if choice > 0 else None

    ext = {"csv": "csv", "excel": "xlsx", "json": "json"}[fmt]
    default_name = f"export_{app_id or 'all'}.{ext}"
    output = click.prompt(f"输出文件名", type=str, default=default_name)

    if fmt == "csv":
        db.export_to_csv(output, app_id)
    elif fmt == "excel":
        db.export_to_excel(output, app_id)
    else:
        db.export_to_json(output, app_id)

    click.echo(f"\n✅ 已导出到: {output}")


def interactive_dashboard():
    """交互式启动仪表盘"""
    click.echo("\n🌐 启动仪表盘\n")

    port = click.prompt("端口号", type=int, default=8501)

    click.echo(f"🚀 启动中... http://localhost:{port}")
    click.echo("按 Ctrl+C 停止\n")

    import subprocess

    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "src/steam_review/dashboard/dashboard.py",
            "--server.port",
            str(port),
        ],
        env=env,
    )


# ============ 快速命令 ============


@cli.command()
@click.option("--app-id", "-a", default="2277560", help="Steam App ID (默认: 2277560)")
@click.option("--limit", "-l", default=0, type=int, help="评论数量 (0=全部)")
def scrape(app_id, limit):
    """📥 爬取 Steam 评论

    示例:
        steam-review scrape                    # 爬取 WUCHANG
        steam-review scrape -a 2897760        # 爬取指定游戏
        steam-review scrape -l 100            # 爬取 100 条
    """
    try:
        asyncio.run(scrape_main(app_id, limit, False))
    except KeyboardInterrupt:
        click.echo("\n⚠️ 操作已取消")
        sys.exit(130)
    except Exception as e:
        handle_error(e)


@cli.command()
@click.argument("file", required=False)
def analyze(file):
    """📊 分析评论数据

    示例:
        steam-review analyze                    # 分析最新文件
        steam-review analyze data/game.csv     # 分析指定文件
    """
    if not file:
        csv_files = list(Path(".").glob("*_reviews.csv"))
        if not csv_files:
            click.echo("❌ 未找到 CSV 文件")
            return
        file = max(csv_files, key=lambda x: x.stat().st_mtime)
        click.echo(f"📁 使用: {file.name}")

    try:
        from src.steam_review.full_analysis import generate_full_analysis

        generate_full_analysis(str(file), "plots")
        click.echo("✅ 完成! 图表在 plots/")
    except KeyboardInterrupt:
        click.echo("\n⚠️ 操作已取消")
        sys.exit(130)
    except Exception as e:
        handle_error(e)


@cli.command()
@click.option("--app-id", "-a", help="App ID筛选")
def stats(app_id):
    """📈 查看统计数据

    示例:
        steam-review stats              # 查看所有游戏
        steam-review stats -a 2277560  # 查看指定游戏
    """
    try:
        db = get_database()
        games = db.get_all_games()

        if app_id:
            games = [g for g in games if str(g["app_id"]) == str(app_id)]

        if not games:
            click.echo("❌ 数据库为空，请先爬取数据")
            return

        for g in games:
            name = config.get_game_name(g["app_id"])
            total = g["total"]
            pos = g["positive"]
            rate = pos / total * 100 if total else 0

            bar = "█" * int(rate / 5) + "░" * (20 - int(rate / 5))
            click.echo(f"\n{name}")
            click.echo(f"  App ID: {g['app_id']}")
            click.echo(f"  总计: {total} | 好评: {pos} ({rate:.1f}%)")
            click.echo(f"  [{bar}]")
    except KeyboardInterrupt:
        click.echo("\n⚠️ 操作已取消")
        sys.exit(130)
    except Exception as e:
        handle_error(e)


@cli.command()
@click.option(
    "--format", "-f", type=click.Choice(["csv", "excel", "json"]), default="csv"
)
@click.option("--app-id", "-a", help="App ID")
@click.option("--output", "-o", help="输出文件")
def export(format, app_id, output):
    """💾 导出数据

    示例:
        steam-review export                    # 导出 CSV
        steam-review export -f excel          # 导出 Excel
        steam-review export -a 2277560        # 导出指定游戏
    """
    db = get_database()

    if not output:
        ext = format
        app_str = app_id or "all"
        output = f"export_{app_str}.{ext}"

    if format == "csv":
        db.export_to_csv(output, app_id)
    elif format == "excel":
        db.export_to_excel(output, app_id)
    else:
        db.export_to_json(output, app_id)

    click.echo(f"✅ 已导出: {output}")


@cli.command()
@click.option("--port", "-p", default=8501, type=int)
def dashboard(port):
    """🌐 启动 Web 仪表盘

    示例:
        steam-review dashboard          # 默认端口 8501
        steam-review dashboard -p 8080  # 指定端口
    """
    click.echo(f"🚀 启动仪表盘: http://localhost:{port}")
    import subprocess

    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "src/steam_review/dashboard/dashboard.py",
            "--server.port",
            str(port),
        ],
        env=env,
    )


@cli.command()
def init():
    """⚙️ 初始化项目"""
    dirs = ["data", "plots", "logs"]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
        click.echo(f"✓ {d}/")

    if not Path("config.json").exists():
        cfg = {"game_names": {}}
        import json

        with open("config.json", "w") as f:
            json.dump(cfg, f, indent=2)
        click.echo("✓ config.json")

    click.echo("\n✅ 初始化完成!")


def main():
    cli()


if __name__ == "__main__":
    main()
