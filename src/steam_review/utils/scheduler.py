import logging
import schedule
import time
import asyncio
from typing import Callable, Dict, List
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class TaskScheduler:
    def __init__(self):
        self.tasks: Dict[str, dict] = {}
        self.running = False
        
    def add_scrape_task(self, app_id: str, interval_hours: int = 24, limit: int = 100):
        task_name = f"scrape_{app_id}"
        
        async def task():
            from steam_review_scraper import main as scrape_main
            logger.info(f"Running scheduled scrape for {app_id}")
            await scrape_main(app_id, limit, incremental=True)
        
        self.tasks[task_name] = {
            "func": lambda: asyncio.run(task()),
            "interval": interval_hours,
            "type": "scrape",
            "app_id": app_id
        }
        
        logger.info(f"Added scheduled scrape task: {task_name} every {interval_hours} hours")
        
    def add_analyze_task(self, file_path: str, interval_hours: int = 24):
        task_name = f"analyze_{file_path}"
        
        async def task():
            from analyze_reviews import main as analyze_main
            logger.info(f"Running scheduled analysis for {file_path}")
            await analyze_main(file_path, save_to_db=True)
        
        self.tasks[task_name] = {
            "func": task,
            "interval": interval_hours,
            "type": "analyze",
            "file_path": file_path
        }
        
        logger.info(f"Added scheduled analyze task: {task_name} every {interval_hours} hours")
        
    def start(self):
        if self.running:
            logger.warning("Scheduler already running")
            return
            
        for task_name, task_info in self.tasks.items():
            interval = task_info["interval"]
            
            if task_info["type"] == "scrape":
                schedule.every(interval).hours.do(task_info["func"])
            elif task_info["type"] == "analyze":
                schedule.every(interval).hours.do(task_info["func"])
        
        self.running = True
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
        
        logger.info(f"Scheduler started with {len(self.tasks)} tasks")
        
    def stop(self):
        self.running = False
        schedule.clear()
        logger.info("Scheduler stopped")
        
    def list_tasks(self) -> List[Dict]:
        return [
            {
                "name": name,
                "type": info["type"],
                "interval_hours": info["interval"],
                "next_run": schedule.next_run() if self.running else None
            }
            for name, info in self.tasks.items()
        ]


def run_scheduler_daemon(app_ids: List[str], interval_hours: int = 24):
    scheduler = TaskScheduler()
    
    for app_id in app_ids:
        scheduler.add_scrape_task(app_id, interval_hours)
    
    scheduler.start()
    
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        scheduler.stop()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run scheduled tasks")
    parser.add_argument("--app_ids", nargs="+", default=["2277560"],
                        help="App IDs to scrape")
    parser.add_argument("--interval", type=int, default=24,
                        help="Interval in hours")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    run_scheduler_daemon(args.app_ids, args.interval)
