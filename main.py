import argparse
import steam_review_scraper
import analyze_reviews
import asyncio
import os

async def run_scraper(app_id, limit=None):
    """Runs the steam_review_scraper.py script."""
    print(f"Running scraper for App ID: {app_id}, Limit: {limit if limit else 'No Limit'}")
    output_filename = await steam_review_scraper.main(app_id, limit)
    print("Scraper finished successfully.")
    return output_filename

async def run_analyzer(file_path):
    """Runs the analyze_reviews.py script."""
    print("Running analyzer...")
    await analyze_reviews.main(file_path)
    print("Analyzer finished successfully. Check the 'plots' directory for visualizations.")

async def main():
    parser = argparse.ArgumentParser(description="Steam Review Analysis Project Entry Point")
    parser.add_argument("--scrape", action="store_true", help="Run the Steam review scraper.")
    parser.add_argument("--analyze", action="store_true", help="Run the review analyzer.")
    parser.add_argument("--all", action="store_true", help="Run both scraper and analyzer sequentially.")
    parser.add_argument("--app_id", type=int, help="Steam Application ID for scraping (required if --scrape or --all is used).")
    parser.add_argument("--limit", type=int, help="Limit the number of reviews to fetch (for scraper).")
    parser.add_argument("--file_path", type=str, help="Path to the reviews CSV file for analysis (required if --analyze is used alone).")

    args = parser.parse_args()

    if not (args.scrape or args.analyze or args.all):
        parser.print_help()
        return

    output_filename = None
    if args.scrape or args.all:
        if not args.app_id:
            print("Error: --app_id is required when using --scrape or --all.")
            return
        output_filename = await run_scraper(str(args.app_id), args.limit)
    
    if args.analyze or args.all:
        file_to_analyze = None
        if args.file_path: # Prioritize file_path if provided
            file_to_analyze = args.file_path
        elif output_filename: # Use the scraped file if available
            file_to_analyze = output_filename
        
        if not file_to_analyze:
            print("Error: No file to analyze. Please run scraper first, specify --file_path, or use --all.")
            return
        
        if not os.path.exists(file_to_analyze):
            print(f"Error: The specified file for analysis does not exist: {file_to_analyze}")
            return

        await run_analyzer(file_to_analyze)

if __name__ == "__main__":
    asyncio.run(main())
