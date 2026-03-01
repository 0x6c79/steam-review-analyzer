# Steam Review Analytics Codebase - Complete Analysis

## Project Overview

**Steam Review Analyzer** is a comprehensive system for scraping, storing, analyzing, and visualizing Steam game reviews. It provides multiple interfaces (Web Dashboard, API, CLI) and advanced analytics capabilities including sentiment analysis, topic modeling, and trend prediction.

**Tech Stack:**
- **Backend**: Python 3.12, FastAPI, SQLite
- **Frontend**: Streamlit (Web Dashboard)
- **Data Processing**: Pandas, NumPy, Scikit-learn
- **Visualization**: Plotly, Matplotlib, Seaborn
- **NLP**: NLTK (VADER), Transformers (BERT/RoBERTa), LangDetect, Jieba
- **Scraping**: aiohttp (async HTTP), Beautiful Soup (implicit)
- **Deployment**: Docker, Uvicorn, Streamlit Server

---

## 1. DATABASE SCHEMA

### Table: `reviews`

Located in: `/home/v/ai_apx/steam_review/data/reviews.db` (SQLite)

#### Column Definitions:

| Column Name | Data Type | Description | Example |
|------------|-----------|-------------|---------|
| `recommendation_id` | TEXT | PRIMARY KEY - Unique review identifier | "12345678901234567" |
| `app_id` | TEXT | Steam App ID (indexed) | "2277560" |
| `language` | TEXT | Review language | "english" |
| `review` | TEXT | Full review text | "This game is amazing..." |
| `timestamp_created` | INTEGER | Unix timestamp when review posted | 1704067200 |
| `timestamp_updated` | INTEGER | Unix timestamp when review last updated | 1704153600 |
| `voted_up` | INTEGER | Boolean (1/0) - positive (1) or negative (0) | 1 |
| `playtime_forever` | REAL | Total playtime in minutes | 1200.5 |
| `playtime_last_two_weeks` | REAL | Playtime in last 2 weeks (minutes) | 120.0 |
| `author_steam_id` | TEXT | Steam ID of review author | "76561198123456789" |
| `author_num_games_owned` | INTEGER | Number of games owned by author | 250 |
| `author_num_reviews` | INTEGER | Number of reviews written by author | 42 |
| `author_playtime_forever` | REAL | Author's total playtime (minutes) | 5600.0 |
| `written_during_early_access` | INTEGER | Boolean (1/0) - written during EA | 0 |
| `detected_language` | TEXT | Auto-detected language code | "en" |
| `sentiment_score` | REAL | VADER sentiment score (-1 to 1) | 0.75 |
| `review_length` | INTEGER | Character count of review | 450 |
| `scraped_at` | TIMESTAMP | When review was added to database | "2025-03-01 10:30:00" |

#### Indexes:
- `idx_app_id` - ON `app_id` (for fast game filtering)
- `idx_timestamp` - ON `timestamp_created` (for time-series analysis)
- `idx_voted_up` - ON `voted_up` (for sentiment filtering)

#### Data Type Compatibility Notes:
- Timestamps are stored as Unix epoch integers (seconds)
- Boolean values stored as 0/1 integers for SQLite compatibility
- All float values coerced to handle missing data gracefully

---

## 2. DASHBOARD ARCHITECTURE & DATA LOADING

### File: `/src/steam_review/dashboard/dashboard.py`

#### Architecture Overview:

```
Streamlit App
├── Sidebar (Navigation & Filters)
├── Pages:
│   ├── 📊 Overview (Main Dashboard)
│   ├── 🔍 Scrape (Data Collection)
│   ├── 📈 Analysis (CSV Processing)
│   ├── 🔬 Advanced Analytics
│   ├── 💾 Database (Export)
│   └── ⚙️ Settings
└── Data Flow: Database → Cached Functions → Visualizations
```

#### Key Functions:

##### 1. `load_data(app_id=None, limit=5000)`
**Purpose**: Fetch reviews from database with caching
**Location**: Line 52-61
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data(app_id=None, limit=5000):
    db = get_database()
    df = db.get_reviews(app_id, limit)
    # Fixes timestamp parsing from Unix to datetime
    if 'timestamp_created' in df.columns:
        df['timestamp_created'] = pd.to_datetime(df['timestamp_created'], unit='s', errors='coerce')
    return df
```

**Parameters:**
- `app_id` (optional): Filter by Steam app ID
- `limit` (default=5000): Max reviews to fetch

**Returns**: Pandas DataFrame with cleaned data

##### 2. `load_stats(app_id=None)`
**Purpose**: Get aggregated statistics
**Location**: Line 64-67
```python
@st.cache_data(ttl=300)
def load_stats(app_id=None):
    db = get_database()
    return db.get_stats(app_id)
```

**Returns**: Dict with keys:
- `total`: Total review count
- `positive`: Count of positive reviews (voted_up=1)
- `negative`: Count of negative reviews (voted_up=0)

##### 3. `get_csv_files()`
**Purpose**: List CSV files in data directory
**Location**: Line 70-74
- Scans `data/` for `*_reviews.csv` files
- Sorts by modification time (newest first)

#### Data Flow in Overview Page (Line 138-362):

1. **Sidebar Data Selection** (Line 90-134)
   - Get all unique app_ids from database
   - Display as "Game Name (App ID)" dropdown
   - User selects game or "All"

2. **Load Data** (Line 141-142)
   - `load_data(app_id_filter, 5000)` fetches reviews
   - `load_stats(app_id_filter)` gets aggregated stats

3. **Render Visualizations** (Line 168-361)
   - **Stats Row**: Total, Positive, Negative, Positive Rate
   - **Row 1**: Sentiment Distribution (pie), Language Distribution (bar)
   - **Row 2**: Reviews Over Time (bar), Positive Rate Trend (line)
   - **Row 3**: Playtime Distribution (histogram), Review Length Distribution
   - **Row 4**: Early Access Analysis, Steam Deck Compatibility
   - **Row 5**: Generated Analysis Charts from `plots/` directory
   - **Recent Reviews**: Table of last 10 reviews

#### Caching Strategy:

```python
@st.cache_data(ttl=300)  # Cache expires after 300 seconds
```
- **TTL**: 5 minutes (300 seconds)
- **Invalidation**: Manual via `st.cache_data.clear()`
- **Scope**: Per session
- **Purpose**: Avoid re-querying database on every user interaction

#### Data Transformation in Dashboard:

1. **Timestamp Conversion** (Line 224, 239)
   - Convert Unix timestamps to datetime for time-series plots
   - Handle parsing errors with `errors='coerce'`

2. **Playtime Binning** (Line 262-265)
   ```python
   bins = [0, 1, 5, 10, 20, 50, 100, 200, 500]
   labels = ['<1h', '1-5h', '5-10h', '10-20h', '20-50h', '50-100h', '100-200h', '200-500h']
   df_copy['playtime_bin'] = pd.cut(df_copy['playtime_hours'], bins=bins, labels=labels)
   ```

3. **Review Length Binning** (Line 280-282)
   ```python
   bins = [0, 50, 100, 200, 500, 1000, 5000]
   labels = ['<50', '50-100', '100-200', '200-500', '500-1000', '>1000']
   ```

4. **Daily Aggregation** (Line 223-226)
   ```python
   daily = df_copy.set_index('date').resample('D')['voted_up'].agg(['count', 'sum'])
   daily['positive_rate'] = daily['sum'] / daily['count']
   ```

---

## 3. DATABASE ACCESS & QUERIES

### File: `/src/steam_review/storage/database.py`

#### Class: `ReviewDatabase`

##### Constructor: `__init__(db_path=None)`
- **Default Path**: `data/reviews.db` (from config)
- **Initialization**: Creates table and indexes on first run

##### Method: `get_reviews(app_id=None, limit=None)`
**Location**: Line 99-136
**Query Pattern**:
```sql
SELECT * FROM reviews
WHERE app_id = ? (if app_id provided)
ORDER BY timestamp_created DESC
LIMIT ? (if limit provided)
```

**Data Cleaning**:
- Converts timestamp columns to numeric (Unix epoch)
- Fixes boolean columns from string representations ('True'/'False') to int (1/0)
- Drops columns with all NaN values
- Handles Streamlit Arrow compatibility issues

**Returns**: Pandas DataFrame

##### Method: `get_stats(app_id=None)`
**Location**: Line 138-151
**Query Pattern**:
```sql
SELECT COUNT(*) as total, SUM(voted_up) as positive
FROM reviews
WHERE app_id = ? (if app_id provided)
```

**Returns**: Dict
```python
{
    'total': int,
    'positive': int,
    'negative': int (calculated as total - positive)
}
```

##### Method: `insert_reviews(df)`
**Location**: Line 51-84
**Process**:
1. Check for existing review IDs to avoid duplicates
2. Filter DataFrame to only include new reviews
3. Handle column naming inconsistencies (app_id vs appid)
4. Insert only valid columns that exist in table schema
5. Return count of inserted reviews

**Returns**: int (count of new reviews inserted)

##### Method: `get_existing_ids()`
**Location**: Line 86-92
**Returns**: Set of all recommendation_ids in database

##### Method: `export_to_csv/excel/json(path, app_id=None)`
**Location**: Line 153-166
- Calls `get_reviews()` to fetch data
- Exports to specified format
- Returns absolute path and logged confirmation

---

## 4. CURRENT FILTERING CAPABILITIES

### Available Filters:

#### A. **In Dashboard** (dashboard.py)
1. **Game/App ID Filter** (Line 112-117)
   - Dropdown selector: "All" or specific game
   - Filters all dashboard metrics and charts
   - Passed to `load_data()` and `load_stats()`

2. **Language Filter** (Line 200-213, advanced_analytics_page.py)
   - Visible in language distribution chart
   - Used for language-specific keyword analysis

3. **Early Access Filter** (Line 298-311)
   - Visual breakdown of reviews written during EA
   - Positive rate comparison

4. **Review Time Filter** (Implicit through SQL query)
   - `ORDER BY timestamp_created DESC` always used
   - Charts aggregate by day/week

#### B. **In API** (api.py)

```python
# GET /reviews
- app_id: Optional[str]    # Filter by app
- language: Optional[str]  # Filter by language
- limit: int (default=10)  # Max results

# GET /stats
- app_id: Optional[str]

# GET /export/{format}
- app_id: Optional[str]
- format: 'csv' | 'excel' | 'json'
```

#### C. **In Database** (database.py)
- `app_id` filtering (WHERE app_id = ?)
- `limit` parameter
- No advanced filtering (must be done in pandas)

### Limitations:

**Current filtering lacks:**
- Sentiment filtering (voted_up is stored but not exposed in UI)
- Playtime range filtering
- Date range filtering
- Review length filtering
- Language-specific filtering in main dashboard
- Text search/keyword filtering
- Author reputation filtering
- Early access specific views (only comparison shown)

---

## 5. DATA PIPELINE & FLOW

### Complete Data Journey:

```
1. SCRAPING (steam_review_scraper.py)
   ├── Async HTTP requests to Steam API
   ├── Flatten nested JSON (author -> author.field)
   ├── Deduplicate using recommendation_id
   └── CSV Output: *_reviews.csv

2. DATABASE INSERTION (database.py → ReviewDatabase.insert_reviews())
   ├── Load existing IDs for deduplication
   ├── Column mapping & validation
   ├── SQLite INSERT
   └── Index creation

3. ANALYSIS (full_analysis.py → generate_full_analysis())
   ├── Language Detection (langdetect)
   ├── Sentiment Analysis (VADER + BERT)
   ├── Keyword Extraction (NLTK + TF-IDF)
   ├── Topic Modeling (LDA)
   ├── Correlation Analysis
   ├── Time Series Analysis
   └── Plot Generation

4. WEB DASHBOARD (dashboard.py)
   ├── Load from DB via load_data()
   ├── Transform timestamps & bins
   ├── Render Streamlit components
   ├── Display interactive charts (Plotly)
   └── Show generated analysis images

5. API SERVING (api.py)
   ├── FastAPI endpoint routing
   ├── Query parameter validation
   ├── DB access with filtering
   └── Response serialization (Pydantic)
```

---

## 6. KEY DATA STRUCTURES & TYPES

### DataFrame Columns After Loading:

**From Database** (`database.py`):
- All columns from reviews table (see Schema section)
- Data types:
  - TEXT → str
  - INTEGER → int
  - REAL → float
  - TIMESTAMP → datetime64[ns] (after conversion)

**After Dashboard Transform** (dashboard.py):
- `date`: datetime64[ns] (converted from timestamp_created)
- `playtime_hours`: float (converted from minutes)
- `playtime_bin`: category (binned playtime)
- `review_length`: int (character count)
- `length_bin`: category (binned length)
- `sentiment_intensity`: str (from advanced_analyzer)
- `quality_score`: float (0-100)

### Pydantic Models (API):

```python
class Review(BaseModel):
    recommendation_id: str
    app_id: Optional[str]
    language: Optional[str]
    review: Optional[str]
    voted_up: bool
    timestamp_created: int

class Stats(BaseModel):
    total: int
    positive: int
    negative: int
    positive_rate: float
```

---

## 7. ANALYSIS MODULES

### Available Analysis:

**Location**: `/src/steam_review/analysis/`

| Module | Purpose | Key Functions |
|--------|---------|----------------|
| `sentiment_analysis.py` | VADER sentiment scoring | `analyze_sentiment()` |
| `advanced_sentiment.py` | BERT/RoBERTa models | Deep sentiment understanding |
| `keyword_analysis.py` | TF-IDF keyword extraction | Language-specific analysis |
| `keyword_extractor.py` | Advanced keyword/topic extraction | `extract_keywords()`, `extract_topics()` |
| `topic_modeling.py` | LDA/NMF topic discovery | `extract_topics()` |
| `time_series_analysis.py` | Temporal trend analysis | `analyze_time_series()` |
| `correlation_analysis.py` | Feature correlation | `analyze_correlation()` |
| `trend_prediction.py` | Predict future sentiment trends | ML-based forecasting |
| `advanced_analyzer.py` | Multi-dimensional analysis | Sentiment intensity, quality scoring, issue detection |
| `game_benchmarking.py` | Compare games | Cross-game comparison metrics |

### Advanced Analyzer (advanced_analyzer.py):

**AdvancedReviewAnalyzer Class** capabilities:

1. **Sentiment Intensity**: 4 levels
   - Very Positive, Positive, Negative, Very Negative

2. **Quality Scoring**: 0-100 scale
   - Factors: length (25pts), detail (25pts), structure (20pts), helpfulness (30pts)

3. **Issue Detection**: Categorized problems
   - Performance, Graphics, Gameplay, Story/Content, Audio, Network/Multiplayer

4. **Player Segmentation**: By playtime/engagement
   - Heavy players, casual players, one-time buyers

5. **Temporal Trends**: Time-based analysis
   - Daily/weekly aggregations and rate calculations

---

## 8. PROJECT STRUCTURE

```
/home/v/ai_apx/steam_review/
├── src/steam_review/
│   ├── storage/
│   │   ├── database.py          # SQLite wrapper (ReviewDatabase class)
│   │   ├── auto_import.py       # Auto CSV import
│   │   └── export_cli.py        # Export utilities
│   ├── dashboard/
│   │   ├── dashboard.py         # Main Streamlit app
│   │   ├── advanced_analytics_page.py  # Advanced features
│   │   └── generate_report.py   # PDF report generation
│   ├── scraper/
│   │   └── steam_review_scraper.py    # Async Steam API client
│   ├── analysis/
│   │   ├── sentiment_analysis.py
│   │   ├── advanced_analyzer.py
│   │   ├── keyword_analysis.py
│   │   ├── topic_modeling.py
│   │   ├── time_series_analysis.py
│   │   └── ... (11 analysis modules total)
│   ├── api/
│   │   └── api.py               # FastAPI REST endpoints
│   ├── cli/
│   │   └── cli.py               # Command-line interface
│   ├── gui/
│   │   ├── gui.py              # PyQt GUI (legacy)
│   │   └── gui_simple.py
│   ├── utils/
│   │   ├── utils.py            # Helper functions
│   │   ├── scheduler.py        # Task scheduling
│   │   └── alerts.py           # Notification system
│   ├── config.py               # Configuration & game names
│   ├── full_analysis.py        # Orchestrator for full analysis
│   └── main.py                 # Entry point
├── data/
│   ├── reviews.db              # SQLite database
│   └── *_reviews.csv           # Scraped CSV files
├── plots/                       # Generated visualization PNGs
├── requirements.txt             # Python dependencies
└── docker-compose.yml           # Docker setup
```

---

## 9. DEPENDENCIES & IMPORTS

### Key External Libraries:

**Data Processing**:
- `pandas` (2.3.1) - DataFrames, CSV/Excel I/O
- `numpy` (2.3.2) - Numerical arrays
- `sqlite3` - Built-in, database access

**Async/HTTP**:
- `aiohttp` (3.12.15) - Async HTTP requests
- `asyncio` - Async runtime

**ML/NLP**:
- `nltk` (3.9.1) - VADER sentiment analyzer
- `transformers` (4.48.2) - BERT/RoBERTa models
- `scikit-learn` (1.6.1) - ML algorithms
- `langdetect` (1.0.9) - Language detection
- `jieba` (0.42.1) - Chinese tokenization

**Visualization**:
- `matplotlib` (3.10.5) - Static plots
- `seaborn` (0.13.2) - Statistical plots
- `plotly` (6.0.0) - Interactive charts
- `wordcloud` (1.9.4) - Word cloud generation
- `pillow` (11.3.0) - Image processing

**Web Frameworks**:
- `streamlit` (1.42.2) - Dashboard UI
- `fastapi` (0.115.12) - REST API
- `uvicorn` (0.34.0) - ASGI server

**Utilities**:
- `schedule` (1.2.2) - Job scheduling
- `tqdm` (4.67.1) - Progress bars
- `reportlab` (4.2.5) - PDF generation
- `requests` (2.32.3) - HTTP client (sync)
- `pydantic` (2.10.6) - Data validation
- `torch` (2.5.1) - PyTorch for transformers
- `scipy` (1.17.1) - Scientific computing
- `openpyxl` (3.1.5) - Excel support

---

## 10. KEY FUNCTIONS SUMMARY

### Database Module (`storage/database.py`)

| Function | Input | Output | Purpose |
|----------|-------|--------|---------|
| `ReviewDatabase.get_reviews()` | app_id, limit | DataFrame | Fetch reviews with optional filtering |
| `ReviewDatabase.get_stats()` | app_id | Dict | Get total/positive/negative counts |
| `ReviewDatabase.insert_reviews()` | DataFrame | int | Insert new reviews, return count |
| `ReviewDatabase.export_to_csv()` | path, app_id | None | Export reviews to CSV file |
| `ReviewDatabase.export_to_excel()` | path, app_id | None | Export reviews to Excel file |
| `ReviewDatabase.export_to_json()` | path, app_id | None | Export reviews to JSON file |
| `ReviewDatabase.get_existing_ids()` | - | Set | Get all recommendation_ids in DB |
| `ReviewDatabase.get_table_columns()` | - | Set | Get valid column names for INSERT |

### Dashboard Module (`dashboard/dashboard.py`)

| Function | Input | Output | Purpose |
|----------|-------|--------|---------|
| `load_data()` | app_id, limit | DataFrame | Load & cache reviews from DB |
| `load_stats()` | app_id | Dict | Load & cache stats from DB |
| `get_csv_files()` | - | List[str] | List CSV files in data/ |
| `run_scrape()` | app_id, limit | str | Execute scraper async |
| `run_analyze()` | csv_file, save_db | None | Run full analysis pipeline |

### Scraper Module (`scraper/steam_review_scraper.py`)

| Function | Purpose | Key Features |
|----------|---------|--------------|
| `get_app_details()` | Fetch game name from Steam API | Async, error handling |
| `get_reviews()` | Fetch paginated reviews from Steam | Rate-limit handling, retries |
| `flatten_review()` | Convert nested JSON to flat dict | Flatten author data |
| `main()` | Orchestrator | Async pagination, deduplication, CSV output |

### API Module (`api/api.py`)

| Endpoint | Method | Parameters | Response |
|----------|--------|-----------|----------|
| `/` | GET | - | {"message": "...", "version": "..."} |
| `/reviews` | GET | app_id, language, limit | List[Review] |
| `/reviews/{id}` | GET | - | Review |
| `/stats` | GET | app_id | Stats |
| `/languages` | GET | app_id | {"languages": {...}} |
| `/export/{format}` | GET | app_id, format | FileResponse |

---

## 11. CURRENT LIMITATIONS & GAPS

### Filtering:
- No advanced query builder (only app_id in DB layer)
- No sentiment range filtering
- No date range picker
- No text search/regex support
- Language filtering only in API, not main dashboard

### Performance:
- No pagination (loads all results then limits)
- Cache TTL is short (5 min) for large datasets
- No database indexing on language/detected_language

### Data Quality:
- Relies on pandas coercion for type conversions
- No validation schema before DB insert
- Missing value handling is implicit

### UI/UX:
- Single app selection in sidebar (should support multi-select)
- No bulk operations
- Advanced filters hidden in advanced_analytics page
- Limited export options (CSV/Excel/JSON only, no database snapshots)

---

## Summary Table

| Aspect | Technology/Approach | Location |
|--------|-------------------|----------|
| **Database** | SQLite (19 columns, 3 indexes) | `data/reviews.db` |
| **Web UI** | Streamlit (6 pages, Plotly charts) | `dashboard/dashboard.py` |
| **REST API** | FastAPI (6 endpoints) | `api/api.py` |
| **Data Pipeline** | Async scraper → CSV → DB → Analysis | `scraper/` → `storage/` → `analysis/` |
| **Caching** | Streamlit @st.cache_data (TTL=300s) | `dashboard.py` lines 51, 64 |
| **Filtering** | SQL WHERE clause + pandas operations | `database.py` get_reviews() |
| **Analysis** | 14 specialized modules (sentiment, topic, trends) | `analysis/` directory |
| **Export** | CSV, Excel, JSON | `database.py` export methods + API |

