import asyncio
import aiohttp
import json
import csv
import urllib.parse
from aiohttp import ClientTimeout

async def get_reviews(session, app_id, cursor='*', retries=5, backoff_factor=1):
    url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&filter=recent&language=all&day_range=9223372036854775807&review_type=all&purchase_type=all"
    if cursor and cursor != '*':
        url += f"&cursor={urllib.parse.quote(cursor)}"

    for attempt in range(retries):
        try:
            timeout = ClientTimeout(total=10)
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                wait_time = backoff_factor * (2 ** attempt)
                print(f"Retrying in {wait_time:.2f} seconds...")
                await asyncio.sleep(wait_time)
            else:
                print(f"Max retries reached for {url}")
                return None
    return None

def flatten_review(review):
    review_flat = review.copy()
    author_data = review_flat.pop('author', {})
    for key, value in author_data.items():
        review_flat[f'author.{key}'] = value
    return review_flat

async def main():
    app_id = "2277560"
    all_reviews = []
    cursor = '*'
    MAX_CONCURRENT_REQUESTS = 5 # Limit concurrent requests
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession() as session:
        while True:
            async with semaphore:
                reviews_data = await get_reviews(session, app_id, cursor)

            if reviews_data and reviews_data.get('success') == 1:
                reviews = reviews_data.get('reviews', [])
                if not reviews:
                    break
                all_reviews.extend(reviews)
                cursor = reviews_data.get('cursor')
                print(f"Fetched {len(reviews)} reviews. Next cursor: {cursor}")
            else:
                print("Failed to fetch reviews or no more reviews.")
                break

    if all_reviews:
        flattened_reviews = [flatten_review(review) for review in all_reviews]

        # Collect all unique fieldnames from all flattened reviews
        all_fieldnames = set()
        for review_flat in flattened_reviews:
            all_fieldnames.update(review_flat.keys())
        fieldnames = sorted(list(all_fieldnames))

        with open('reviews.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for review_flat in flattened_reviews:
                writer.writerow(review_flat)
        print(f"Successfully saved {len(all_reviews)} reviews to reviews.csv")
    else:
        print("No reviews found.")

if __name__ == "__main__":
    asyncio.run(main())
