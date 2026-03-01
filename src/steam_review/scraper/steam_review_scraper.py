import sys
import os
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
import aiohttp
import csv
import urllib.parse
from aiohttp import ClientTimeout
import logging
import argparse
from src.steam_review import config

config.setup_logging()

DEFAULT_TIMEOUT = ClientTimeout(total=10)


def load_existing_review_ids(csv_path):
    if not os.path.exists(csv_path):
        return set()
    existing_ids = set()
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle both 'recommendation_id' and 'recommendationid'
                rid = row.get('recommendation_id') or row.get('recommendationid')
                if rid:
                    existing_ids.add(rid)
        logging.info(f"Loaded {len(existing_ids)} existing review IDs from {csv_path}")
    except Exception as e:
        logging.warning(f"Could not load existing review IDs: {e}")
    return existing_ids

async def get_app_details(session, app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        async with session.get(url, timeout=DEFAULT_TIMEOUT) as response:
            response.raise_for_status()
            data = await response.json()
            if data and str(app_id) in data and data[str(app_id)].get('success'):
                return data[str(app_id)]['data'].get('name')
            else:
                logging.error(f"Could not retrieve app details for App ID {app_id}.")
                return None
    except aiohttp.ClientError as e:
        logging.error(f"Error fetching app details for App ID {app_id}: {e}")
        return None

async def get_reviews(session, app_id, cursor='*', retries=5, backoff_factor=1):
    url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&filter=all&language=all&day_range=9223372036854775807&review_type=all&purchase_type=all"
    if cursor != '*':
        url += f"&cursor={urllib.parse.quote(cursor)}"

    for attempt in range(retries):
        try:
            await asyncio.sleep(0.5)
            async with session.get(url, timeout=DEFAULT_TIMEOUT) as response:
                if response.status == 429:
                    retry_after = response.headers.get('Retry-After')
                    wait_time = int(retry_after) if retry_after else backoff_factor * (2 ** attempt)
                    logging.warning(f"Rate limit hit (429). Waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                retry_after = e.headers.get('Retry-After')
                wait_time = int(retry_after) if retry_after else backoff_factor * (2 ** attempt)
                logging.warning(f"Rate limit hit (429). Waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logging.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    logging.info(f"Retrying in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logging.error(f"Max retries reached for {url}")
                    return None
        except aiohttp.ClientError as e:
            logging.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                wait_time = backoff_factor * (2 ** attempt)
                logging.info(f"Retrying in {wait_time:.2f} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logging.error(f"Max retries reached for {url}")
                return None
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return None
    return None

def flatten_review(review):
    review_flat = review.copy()
    author_data = review_flat.pop('author', {})
    for key, value in author_data.items():
        review_flat[f'author.{key}'] = value
    return review_flat

def save_checkpoint(app_id, cursor, total_fetched):
    checkpoint_file = f".checkpoint_{app_id}.txt"
    with open(checkpoint_file, 'w') as f:
        f.write(f"{cursor}\n{total_fetched}")

def load_checkpoint(app_id):
    checkpoint_file = f".checkpoint_{app_id}.txt"
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r') as f:
                cursor = f.readline().strip()
                total = int(f.readline().strip())
            os.remove(checkpoint_file)
            logging.info(f"Resuming from checkpoint: cursor={cursor[:50]}..., total={total}")
            return cursor, total
        except:
            pass
    return '*', 0

async def main(app_id, limit=0, incremental=False):
    MAX_CONCURRENT_REQUESTS = 5
    DEFAULT_INCREMENTAL_LIMIT = 1000
    LIMIT = limit if limit is not None else (DEFAULT_INCREMENTAL_LIMIT if incremental else 0)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    header_written = False

    try:
        async with aiohttp.ClientSession() as session:
            game_name = await get_app_details(session, app_id)
            if game_name:
                sanitized_game_name = "".join([c if c.isalnum() or c in (' ', '_', '-') else '_' for c in game_name]).strip()
                output_filename = f"{sanitized_game_name}_{app_id}_reviews.csv"
            else:
                output_filename = f"reviews_{app_id}.csv"
                logging.warning(f"Could not retrieve game name for App ID {app_id}. Using default filename: {output_filename}")

            existing_ids = set()
            if os.path.exists(output_filename):
                existing_ids = load_existing_review_ids(output_filename)
                if existing_ids:
                    logging.info(f"Found {len(existing_ids)} existing reviews in {output_filename}")

            cursor, total_reviews_fetched = load_checkpoint(app_id)
            write_mode = 'a' if os.path.exists(output_filename) else 'w'
            
            with open(output_filename, write_mode, newline='', encoding='utf-8') as csvfile:
                writer = None
                new_reviews_count = 0
                consecutive_failures = 0

                while True:
                    async with semaphore:
                        reviews_data = await get_reviews(session, app_id, cursor)
                        consecutive_failures = 0

                    if reviews_data and reviews_data.get('success') == 1:
                        reviews = reviews_data.get('reviews', [])
                        if not reviews:
                            logging.info("No more reviews to fetch.")
                            break

                        flattened_reviews = [flatten_review(review) for review in reviews]
                        
                        for r in flattened_reviews:
                            rid = r.get('recommendation_id') or r.get('recommendationid')
                            r['recommendation_id'] = rid

                        new_reviews = [r for r in flattened_reviews if r.get('recommendation_id') not in existing_ids]

                        if new_reviews:
                            if not header_written:
                                all_fieldnames = set()
                                for review_flat in flattened_reviews:
                                    all_fieldnames.update(review_flat.keys())
                                fieldnames = sorted(list(all_fieldnames))
                                
                                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                                if write_mode == 'w':
                                    writer.writeheader()
                                header_written = True
                                logging.info("CSV header written.")

                            writer.writerows(new_reviews)
                            csvfile.flush()
                            new_reviews_count += len(new_reviews)
                            
                            for r in new_reviews:
                                existing_ids.add(r.get('recommendation_id'))
                        

                        total_reviews_fetched += len(flattened_reviews)
                        new_cursor = reviews_data.get('cursor')
                        
                        if not new_cursor or new_cursor == cursor:
                            logging.info("No more reviews available (cursor unchanged).")
                            break
                        cursor = new_cursor
                        
                        save_checkpoint(app_id, cursor, total_reviews_fetched)

                        if LIMIT > 0 and total_reviews_fetched >= LIMIT:
                            logging.info(f"Reached the limit of {LIMIT} reviews. Stopping.")
                            break
                        
                        if incremental and not new_reviews and total_reviews_fetched > 100:
                            logging.info("All new reviews already exist. Stopping.")
                            break
                            
                        logging.info(f"Fetched {len(flattened_reviews)} reviews, {len(new_reviews)} new. Total: {total_reviews_fetched}")
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= 5:
                            logging.error("Failed to fetch reviews 5 times consecutively. Saving checkpoint and exiting.")
                            save_checkpoint(app_id, cursor, total_reviews_fetched)
                            break
                        logging.warning(f"Failed to fetch reviews (attempt {consecutive_failures}/5). Retrying...")
                        await asyncio.sleep(2)

            if os.path.exists(f".checkpoint_{app_id}.txt"):
                os.remove(f".checkpoint_{app_id}.txt")
                
            mode_str = "incremental" if incremental else "full"
            logging.info(f"Successfully saved {new_reviews_count} new reviews ({mode_str} mode) to {output_filename}")
            
            # Auto-import to database
            logging.info("Auto-importing reviews to database...")
            try:
                import pandas as pd
                from src.steam_review.storage.database import get_database
                
                df = pd.read_csv(output_filename)
                print(f"   Loaded {len(df)} reviews from {output_filename}")
                
                # Ensure app_id column
                if 'appid' in df.columns and 'app_id' not in df.columns:
                    df['app_id'] = df['appid'].astype(str)
                elif 'app_id' not in df.columns:
                    df['app_id'] = str(app_id)
                
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
                
                # Clean up timestamp columns - convert to numeric (Unix timestamp)
                for col in ['timestamp_created', 'timestamp_updated']:
                    if col in df.columns:
                        # Convert to numeric, handling various formats
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
                count = db.insert_reviews(df)
                
                if count > 0:
                    logging.info(f"✅ Imported {count} reviews to database")
                else:
                    logging.info(f"✅ All reviews already in database")
                    
                # Show updated stats
                db_stats = db.get_stats(str(app_id))
                logging.info(f"📈 Updated database stats - Total: {db_stats['total']}, Positive: {db_stats['positive']}, Negative: {db_stats['negative']}")
                
            except Exception as e:
                logging.warning(f"Auto-import failed: {e}. You can manually import later with: python -m src.steam_review.storage.auto_import")
            
            return output_filename
    except KeyboardInterrupt:
        logging.info("Interrupted by user. Saving checkpoint...")
        if 'cursor' in locals() and 'total_reviews_fetched' in locals():
            save_checkpoint(app_id, cursor, total_reviews_fetched)
            logging.info(f"Checkpoint saved. Run again to resume from {total_reviews_fetched} reviews.")
    except IOError as e:
        logging.error(f"Error writing reviews to CSV: {e}", exc_info=True)
        if 'cursor' in locals() and 'total_reviews_fetched' in locals():
            save_checkpoint(app_id, cursor, total_reviews_fetched)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        if 'cursor' in locals() and 'total_reviews_fetched' in locals():
            save_checkpoint(app_id, cursor, total_reviews_fetched)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Steam reviews for a given App ID.")
    parser.add_argument("--app_id", type=str, default="2277560",
                        help="The Steam App ID to scrape reviews for (default: 2277560).")
    parser.add_argument("--limit", type=int, default=0,
                        help="Maximum number of reviews to fetch (default: 0, means no limit).")
    parser.add_argument("--incremental", action="store_true",
                        help="Enable incremental mode: only fetch new reviews not already in CSV.")
    args = parser.parse_args()
    asyncio.run(main(args.app_id, args.limit, args.incremental))
