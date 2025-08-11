import asyncio
import aiohttp
import csv
import urllib.parse
from aiohttp import ClientTimeout
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def get_app_details(session, app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        timeout = ClientTimeout(total=10)
        async with session.get(url, timeout=timeout) as response:
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
            timeout = ClientTimeout(total=10)
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                return await response.json()
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                retry_after = e.headers.get('Retry-After')
                wait_time = int(retry_after) if retry_after else backoff_factor * (2 ** attempt)
                logging.warning(f"Rate limit hit (429). Retrying in {wait_time:.2f} seconds...")
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
    return None

def flatten_review(review):
    review_flat = review.copy()
    author_data = review_flat.pop('author', {})
    for key, value in author_data.items():
        review_flat[f'author.{key}'] = value
    return review_flat

async def main(app_id, limit=0):
    MAX_CONCURRENT_REQUESTS = 5
    LIMIT = limit
    cursor = '*'
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    # Use a flag to write header only once
    header_written = False

    try:
        async with aiohttp.ClientSession() as session:
            game_name = await get_app_details(session, app_id)
            if game_name:
                # Sanitize game name for filename
                sanitized_game_name = "".join([c if c.isalnum() or c in (' ', '_', '-') else '_' for c in game_name]).strip()
                output_filename = f"{sanitized_game_name}_{app_id}_reviews.csv"
            else:
                output_filename = f"reviews_{app_id}.csv"
                logging.warning(f"Could not retrieve game name for App ID {app_id}. Using default filename: {output_filename}")

            with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = None # Initialize writer to None
                total_reviews_fetched = 0
                while True:
                    async with semaphore:
                        reviews_data = await get_reviews(session, app_id, cursor)

                    if reviews_data and reviews_data.get('success') == 1:
                        reviews = reviews_data.get('reviews', [])
                        if not reviews:
                            logging.info("No more reviews to fetch.")
                            break

                        flattened_reviews = [flatten_review(review) for review in reviews]

                        if not header_written:
                            # Collect all unique fieldnames from the first batch of flattened reviews
                            all_fieldnames = set()
                            for review_flat in flattened_reviews:
                                all_fieldnames.update(review_flat.keys())
                            fieldnames = sorted(list(all_fieldnames))
                            
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                            writer.writeheader()
                            header_written = True
                            logging.info("CSV header written.")

                        writer.writerows(flattened_reviews)
                        total_reviews_fetched += len(flattened_reviews)
                        cursor = reviews_data.get('cursor')

                        if LIMIT > 0 and total_reviews_fetched >= LIMIT:
                            logging.info(f"Reached the limit of {LIMIT} reviews. Stopping.")
                            break
                        logging.info(f"Fetched and wrote {len(flattened_reviews)} reviews. Total: {total_reviews_fetched}. Next cursor: {cursor}")
                    else:
                        logging.warning("Failed to fetch reviews or no more reviews.")
                        break
            logging.info(f"Successfully saved {total_reviews_fetched} reviews to {output_filename}")
    except IOError as e:
        logging.error(f"Error writing reviews to CSV: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Steam reviews for a given App ID.")
    parser.add_argument("--app_id", type=str, default="2277560",
                        help="The Steam App ID to scrape reviews for (default: 2277560).")
    parser.add_argument("--limit", type=int, default=0,
                        help="Maximum number of reviews to fetch (default: 0, means no limit).")
    args = parser.parse_args()
    asyncio.run(main(args.app_id, args.limit))
