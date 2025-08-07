# Project Overview

This project contains a Python script (`steam_review_scraper.py`) designed to scrape reviews from Steam for a specified application ID. The script utilizes `aiohttp` for asynchronous HTTP requests, which significantly improves the efficiency and speed of data collection by allowing multiple requests to be made concurrently. The scraped reviews are then processed and saved into a CSV file named `reviews.csv`.

# Building and Running

This project uses a Python virtual environment to manage its dependencies.

## Setup

1.  **Create a virtual environment:**
    ```bash
    python3 -m venv .venv
    ```
2.  **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install aiohttp
    ```

## Running the Scraper

To run the Steam review scraper:

```bash
source .venv/bin/activate && python3 steam_review_scraper.py
```

The script is configured with a 3-minute timeout. If the scraping process exceeds this duration, the program will automatically terminate.

## Running with Real-time Logging

To view the script's output in real-time on the console while also saving it to a log file (`steam_review_scraper.log`):

```bash
source .venv/bin/activate && python3 steam_review_scraper.py | tee steam_review_scraper.log
```

# Development Conventions

*   **Asynchronous Operations:** The script leverages `asyncio` and `aiohttp` for efficient, non-blocking network requests.
*   **Error Handling:** Basic error handling for HTTP requests is implemented to catch `aiohttp.ClientError` exceptions.
*   **Data Flattening:** Nested JSON data, specifically the 'author' dictionary within each review, is flattened into a single level for easier consumption in the CSV output.
*   **Timeout Mechanism:** A global timeout of 3 minutes is implemented for the entire scraping process to prevent indefinite execution.
