import argparse
import subprocess
import os

def run_scraper(app_id, limit=None):
    """Runs the steam_review_scraper.py script."""
    command = ["python3", "steam_review_scraper.py"]
    if app_id:
        command.extend(["--app_id", str(app_id)])
    if limit:
        command.extend(["--limit", str(limit)])
    
    print(f"Running scraper with command: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
        print("Scraper finished successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running scraper: {e}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
    except FileNotFoundError:
        print("Error: python3 command not found. Ensure Python is installed and in your PATH.")

def run_analyzer():
    """Runs the analyze_reviews.py script."""
    command = ["python3", "analyze_reviews.py"]
    print(f"Running analyzer with command: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
        print("Analyzer finished successfully. Check the 'plots' directory for visualizations.")
    except subprocess.CalledProcessError as e:
        print(f"Error running analyzer: {e}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
    except FileNotFoundError:
        print("Error: python3 command not found. Ensure Python is installed and in your PATH.")

def main():
    parser = argparse.ArgumentParser(description="Steam Review Analysis Project Entry Point")
    parser.add_argument("--scrape", action="store_true", help="Run the Steam review scraper.")
    parser.add_argument("--analyze", action="store_true", help="Run the review analyzer.")
    parser.add_argument("--all", action="store_true", help="Run both scraper and analyzer sequentially.")
    parser.add_argument("--app_id", type=int, help="Steam Application ID for scraping (required if --scrape or --all is used).")
    parser.add_argument("--limit", type=int, help="Limit the number of reviews to fetch (for scraper).")

    args = parser.parse_args()

    if not (args.scrape or args.analyze or args.all):
        parser.print_help()
        return

    if args.scrape or args.all:
        if not args.app_id:
            print("Error: --app_id is required when using --scrape or --all.")
            return
        run_scraper(args.app_id, args.limit)
    
    if args.analyze or args.all:
        # Ensure reviews.csv exists if only analyze is run
        if args.analyze and not os.path.exists("reviews.csv"):
            print("Warning: reviews.csv not found. Please run the scraper first or ensure the file exists.")
            # Optionally, you might want to exit here or prompt the user.
            # For now, we'll let the analyzer run and likely fail if reviews.csv is truly missing.
        run_analyzer()

if __name__ == "__main__":
    main()
