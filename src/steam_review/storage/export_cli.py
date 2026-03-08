import argparse
from src.steam_review.storage.database import get_database
from src.steam_review import config

config.setup_logging()


def export_command(args):
    db = get_database()
    
    if args.format == 'csv':
        db.export_to_csv(args.output, args.app_id)
    elif args.format == 'excel':
        db.export_to_excel(args.output, args.app_id)
    elif args.format == 'json':
        db.export_to_json(args.output, args.app_id)
    
    print(f"Exported to {args.output}")


def stats_command(args):
    db = get_database()
    stats = db.get_stats(args.app_id if hasattr(args, 'app_id') else None)
    
    print(f"Total reviews: {stats['total']}")
    print(f"Positive: {stats['positive']}")
    print(f"Negative: {stats['negative']}")
    if stats['total'] > 0:
        print(f"Positive rate: {stats['positive'] / stats['total'] * 100:.1f}%")


def list_command(args):
    db = get_database()
    app_id = args.app_id if hasattr(args, 'app_id') else None
    limit = args.limit if hasattr(args, 'limit') else 10
    df = db.get_reviews(app_id, limit)
    
    if df.empty:
        print("No reviews found")
        return
    
    print(df[['recommendation_id', 'language', 'review', 'voted_up', 'timestamp_created']].to_string())


def main():
    parser = argparse.ArgumentParser(description="Steam Review Export CLI")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export reviews')
    export_parser.add_argument("--format", choices=['csv', 'excel', 'json'], required=True)
    export_parser.add_argument("--output", required=True)
    export_parser.add_argument("--app_id", help="Filter by App ID")
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.add_argument("--app_id", help="Filter by App ID")
    
    # List command
    list_parser = subparsers.add_parser('list', help='List reviews')
    list_parser.add_argument("--app_id", help="Filter by App ID")
    list_parser.add_argument("--limit", type=int, default=10)
    
    args = parser.parse_args()
    
    if args.command == 'export':
        export_command(args)
    elif args.command == 'stats':
        stats_command(args)
    elif args.command == 'list':
        list_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
