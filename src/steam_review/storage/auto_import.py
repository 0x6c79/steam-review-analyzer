#!/usr/bin/env python3
"""
Auto-import script - Automatically imports CSV files into the database
Run from project root:
    python -m src.steam_review.storage.auto_import
"""
import os
import sys

# Get project root (parent of storage directory)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

import pandas as pd
import glob
from tqdm import tqdm
from src.steam_review.storage.database import get_database
from src.steam_review import config


def get_app_name_from_filename(filename):
    """Extract game name from CSV filename"""
    # Format: "Game Name_appid_reviews.csv"
    basename = os.path.basename(filename)
    name_part = basename.replace('_reviews.csv', '')
    parts = name_part.rsplit('_', 1)
    if len(parts) == 2:
        app_id = parts[1]
        game_name = parts[0].replace('_', ' ')
        return game_name, app_id
    return name_part, None


def import_csv_files():
    """Import all CSV files in data directory to database"""
    data_dir = config.PROJECT_ROOT
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(data_dir, 'data', '*_reviews.csv'))
    
    if not csv_files:
        print("No CSV files found to import")
        return
    
    db = get_database()
    
    # Track import stats
    stats = {
        'total_files': len(csv_files),
        'imported': 0,
        'skipped': 0,
        'errors': 0
    }
    
    for csv_file in tqdm(csv_files, desc="Importing CSV files", unit="file"):
        try:
            filename = os.path.basename(csv_file)
            
            df = pd.read_csv(csv_file)
            
            # Ensure app_id column
            if 'appid' in df.columns and 'app_id' not in df.columns:
                df['app_id'] = df['appid'].astype(str)
            
            # Ensure voted_up is 0/1
            if 'voted_up' in df.columns:
                if df['voted_up'].dtype == 'bool':
                    df['voted_up'] = df['voted_up'].astype(int)
                elif df['voted_up'].dtype == 'object':
                    vote_map = {
                        'True': 1, 'False': 0, 
                        True: 1, False: 0
                    }
                    df['voted_up'] = df['voted_up'].map(vote_map).fillna(0).astype(int)
            
            # Clean up timestamp columns - convert to numeric
            for col in ['timestamp_created', 'timestamp_updated']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
            # Clean up boolean columns
            for col in ['is_recommended', 'received_for_free']:
                if col in df.columns and df[col].dtype == 'object':
                    bool_map = {
                        'True': 1, 'False': 0,
                        '1': 1, '0': 0,
                        True: 1, False: 0
                    }
                    df[col] = df[col].map(bool_map).fillna(0).astype(int)
            
            # Insert into database
            count = db.insert_reviews(df)
            
            if count > 0:
                stats['imported'] += 1
            else:
                stats['skipped'] += 1
                
        except Exception as e:
            stats['errors'] += 1
    
    print(f"\n{'='*50}")
    print(f"📊 Import Summary:")
    print(f"   Total files: {stats['total_files']}")
    print(f"   Imported: {stats['imported']}")
    print(f"   Skipped: {stats['skipped']}")
    print(f"   Errors: {stats['errors']}")
    print(f"{'='*50}")
    
    # Show database stats
    db_stats = db.get_stats()
    print(f"\n📈 Database Stats:")
    print(f"   Total reviews: {db_stats['total']}")
    print(f"   Positive: {db_stats['positive']}")
    print(f"   Negative: {db_stats['negative']}")


def import_single_csv(csv_file):
    """Import a single CSV file to database"""
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        return
    
    try:
        print(f"\n📁 Processing: {os.path.basename(csv_file)}")
        
        df = pd.read_csv(csv_file)
        
        # Show progress with tqdm for large files
        if len(df) > 1000:
            df_list = [chunk for chunk in tqdm([df], desc="Reading data", unit="chunk")]
            df = df_list[0]
        
        # Ensure app_id column
        if 'appid' in df.columns and 'app_id' not in df.columns:
            df['app_id'] = df['appid'].astype(str)
        
        # Ensure voted_up is 0/1
        if 'voted_up' in df.columns:
            if df['voted_up'].dtype == 'bool':
                df['voted_up'] = df['voted_up'].astype(int)
            elif df['voted_up'].dtype == 'object':
                vote_map = {
                    'True': 1, 'False': 0, 
                    True: 1, False: 0
                }
                df['voted_up'] = df['voted_up'].map(vote_map).fillna(0).astype(int)
        
        # Clean up timestamp columns - convert to numeric
        for col in ['timestamp_created', 'timestamp_updated']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Clean up boolean columns
        for col in ['is_recommended', 'received_for_free']:
            if col in df.columns and df[col].dtype == 'object':
                bool_map = {
                    'True': 1, 'False': 0,
                    '1': 1, '0': 0,
                    True: 1, False: 0
                }
                df[col] = df[col].map(bool_map).fillna(0).astype(int)
        
        db = get_database()
        
        # Insert into database
        print("Inserting into database...")
        count = db.insert_reviews(df)
        
        if count > 0:
            print(f"✅ Inserted {count} new reviews")
        else:
            print(f"⏭️  No new reviews (already exists)")
        
        # Show database stats
        db_stats = db.get_stats()
        print(f"\n📈 Database Stats:")
        print(f"   Total reviews: {db_stats['total']}")
        print(f"   Positive: {db_stats['positive']}")
        print(f"   Negative: {db_stats['negative']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import_csv_files()
