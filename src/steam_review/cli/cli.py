#!/usr/bin/env python3
"""
Steam Review Analyzer - Unified CLI Tool
Usage: python cli.py <command> [options]
"""
import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(
        description="Steam Review Analyzer - Unified CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape reviews
  python cli.py scrape --app_id 2277560 --limit 1000
  
  # Analyze reviews
  python cli.py analyze "reviews.csv"
  
  # Full pipeline (scrape + analyze + dashboard)
  python cli.py run --app_id 2277560 --limit 500
  
  # Export data
  python cli.py export --format csv --output data.csv
  
  # View stats
  python cli.py stats
  
  # Run web dashboard
  python cli.py dashboard
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape reviews from Steam')
    scrape_parser.add_argument('--app_id', '-a', required=True, help='Steam App ID')
    scrape_parser.add_argument('--limit', '-l', type=int, default=0, help='Max reviews (0=unlimited)')
    scrape_parser.add_argument('--incremental', '-i', action='store_true', help='Incremental update')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze scraped reviews')
    analyze_parser.add_argument('csv_file', nargs='?', help='CSV file to analyze')
    analyze_parser.add_argument('--save_db', '-s', action='store_true', help='Save to database')
    analyze_parser.add_argument('--output', '-o', default='plots', help='Output directory for plots')
    
    # Run command (full pipeline)
    run_parser = subparsers.add_parser('run', help='Full pipeline: scrape + analyze + dashboard')
    run_parser.add_argument('--app_id', '-a', required=True, help='Steam App ID')
    run_parser.add_argument('--limit', '-l', type=int, default=500, help='Max reviews')
    run_parser.add_argument('--save_db', '-s', action='store_true', help='Save to database')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data from database')
    export_parser.add_argument('--format', '-f', choices=['csv', 'excel', 'json'], default='csv')
    export_parser.add_argument('--output', '-o', required=True, help='Output file')
    export_parser.add_argument('--app_id', '-a', help='Filter by App ID')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    stats_parser.add_argument('--app_id', '-a', help='Filter by App ID')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import CSV files to database')
    import_parser.add_argument('--csv', '-c', help='Specific CSV file to import')
    
    # Dashboard command
    dash_parser = subparsers.add_parser('dashboard', help='Launch web dashboard')
    dash_parser.add_argument('--port', '-p', type=int, default=8501, help='Port number')
    
    # Serve command (API)
    serve_parser = subparsers.add_parser('serve', help='Launch API server')
    serve_parser.add_argument('--port', '-p', type=int, default=8000, help='Port number')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute commands
    if args.command == 'scrape':
        from ..scraper.steam_review_scraper import main as scrape_main
        import asyncio
        print(f"Scraping reviews for App ID: {args.app_id}")
        if args.limit:
            print(f"Limit: {args.limit}")
        asyncio.run(scrape_main(args.app_id, args.limit, args.incremental))
        
    elif args.command == 'analyze':
        csv_file = args.csv_file
        if not csv_file:
            # Find latest CSV
            csvs = [f for f in os.listdir('.') if f.endswith('_reviews.csv')]
            if not csvs:
                print("Error: No CSV files found. Run 'scrape' first.")
                return
            csv_file = max(csvs, key=os.path.getmtime)
            print(f"Using latest file: {csv_file}")
        
        from ..full_analysis import generate_full_analysis
        generate_full_analysis(csv_file, args.output)
        
    elif args.command == 'run':
        from ..scraper.steam_review_scraper import main as scrape_main
        from ..full_analysis import generate_full_analysis
        import asyncio
        import glob
        
        # Step 1: Scrape
        print(f"\n{'='*50}")
        print("Step 1: Scraping reviews...")
        print('='*50)
        csv_file = asyncio.run(scrape_main(args.app_id, args.limit, False))
        
        # Step 2: Analyze
        print(f"\n{'='*50}")
        print("Step 2: Analyzing reviews...")
        print('='*50)
        generate_full_analysis(csv_file, 'plots')
        
        print(f"\n{'='*50}")
        print("Done! Dashboard generated.")
        print('='*50)
        
    elif args.command == 'export':
        from ..storage.database import get_database
        db = get_database()
        
        if args.format == 'csv':
            db.export_to_csv(args.output, args.app_id)
        elif args.format == 'excel':
            db.export_to_excel(args.output, args.app_id)
        elif args.format == 'json':
            db.export_to_json(args.output, args.app_id)
        
        print(f"Exported to: {args.output}")
        
    elif args.command == 'stats':
        from ..storage.database import get_database
        db = get_database()
        stats = db.get_stats(args.app_id)
        
        print(f"\n{'='*40}")
        print("Database Statistics")
        print('='*40)
        print(f"Total Reviews: {stats['total']}")
        print(f"Positive:      {stats['positive']}")
        print(f"Negative:      {stats['negative']}")
        if stats['total'] > 0:
            print(f"Positive Rate: {stats['positive']/stats['total']*100:.1f}%")
        
    elif args.command == 'dashboard':
        print(f"Starting Streamlit dashboard on port {args.port}...")
        print(f"Open http://localhost:{args.port} in your browser")
        import subprocess
        import sys
        env = os.environ.copy()
        env['PYTHONPATH'] = 'src'
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', 
                        'src/steam_review/dashboard/dashboard.py', 
                        '--server.port', str(args.port)], env=env)
        
    elif args.command == 'import':
        from ..storage.auto_import import import_csv_files, import_single_csv
        
        if args.csv:
            print(f"Importing CSV: {args.csv}")
            import_single_csv(args.csv)
        else:
            print("Importing all CSV files from data directory...")
            import_csv_files()
    
    elif args.command == 'serve':
        print(f"Starting API server on port {args.port}...")
        print(f"Open http://localhost:{args.port}/docs for API documentation")
        os.system(f"uvicorn src.steam_review.api.api:app --host 0.0.0.0 --port {args.port}")


if __name__ == '__main__':
    main()
