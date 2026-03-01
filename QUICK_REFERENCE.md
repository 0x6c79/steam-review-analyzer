# Steam Review Analytics - Quick Reference Guide

## Database Schema at a Glance

```
TABLE: reviews
┌─────────────────────────────┬─────────┐
│ Column                      │ Type    │
├─────────────────────────────┼─────────┤
│ recommendation_id (PK)      │ TEXT    │
│ app_id (indexed)            │ TEXT    │
│ language                    │ TEXT    │
│ review                      │ TEXT    │
│ timestamp_created (indexed) │ INTEGER │
│ timestamp_updated           │ INTEGER │
│ voted_up (indexed)          │ INTEGER │
│ playtime_forever            │ REAL    │
│ playtime_last_two_weeks     │ REAL    │
│ author_steam_id             │ TEXT    │
│ author_num_games_owned      │ INTEGER │
│ author_num_reviews          │ INTEGER │
│ author_playtime_forever     │ REAL    │
│ written_during_early_access │ INTEGER │
│ detected_language           │ TEXT    │
│ sentiment_score             │ REAL    │
│ review_length               │ INTEGER │
│ scraped_at                  │ TIMESTAMP
└─────────────────────────────┴─────────┘
```

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     STEAM REVIEW ANALYZER                        │
└──────────────────────────────────────────────────────────────────┘

1. DATA COLLECTION
   ┌─────────────────────────┐
   │ Steam API               │
   │ (steam_review_scraper)  │
   └────────────┬────────────┘
                │ Async aiohttp
                ▼
   ┌─────────────────────────┐
   │ CSV Files (*_reviews)   │
   │ (data/ directory)       │
   └────────────┬────────────┘

2. DATA STORAGE
   ┌─────────────────────────┐
   │ SQLite Database         │
   │ (reviews.db)            │
   │ ReviewDatabase class    │
   └────────────┬────────────┘
                │
        ┌───────┴───────┬──────────────┐
        ▼               ▼              ▼
   CSV Export      Excel Export    JSON Export
   (API)           (API)           (API)

3. DATA ANALYSIS
   ┌─────────────────────────┐
   │ Analysis Modules        │
   │ • Sentiment (VADER)     │
   │ • Keywords (TF-IDF)     │
   │ • Topics (LDA)          │
   │ • Time Series           │
   │ • Advanced (BERT)       │
   └────────────┬────────────┘
                │
                ▼
   ┌─────────────────────────┐
   │ Generated Plots         │
   │ (plots/ directory)      │
   └────────────┬────────────┘

4. VISUALIZATION & SERVING
   ┌──────────────────────────────────────┐
   │ Streamlit Dashboard (Port 8501)      │
   │ ├─ Overview                          │
   │ ├─ Scrape                            │
   │ ├─ Analysis                          │
   │ ├─ Advanced Analytics                │
   │ ├─ Database                          │
   │ └─ Settings                          │
   └──────────────────────────────────────┘
   
   ┌──────────────────────────────────────┐
   │ FastAPI (Port 8000)                  │
   │ ├─ GET /reviews                      │
   │ ├─ GET /stats                        │
   │ ├─ GET /languages                    │
   │ └─ GET /export/{format}              │
   └──────────────────────────────────────┘
```

## Core Classes & Methods

### ReviewDatabase
```python
class ReviewDatabase:
    def __init__(db_path=None)
    
    # QUERIES
    def get_reviews(app_id=None, limit=None) -> DataFrame
    def get_stats(app_id=None) -> Dict[str, int]
    def get_existing_ids() -> Set[str]
    def get_table_columns() -> Set[str]
    
    # MUTATIONS
    def insert_reviews(df) -> int  # Returns count inserted
    
    # EXPORT
    def export_to_csv(path, app_id=None)
    def export_to_excel(path, app_id=None)
    def export_to_json(path, app_id=None)
```

### Streamlit Dashboard Functions
```python
@st.cache_data(ttl=300)
def load_data(app_id=None, limit=5000) -> DataFrame

@st.cache_data(ttl=300)
def load_stats(app_id=None) -> Dict

def get_csv_files() -> List[str]
def run_scrape(app_id, limit) -> str
def run_analyze(csv_file, save_db) -> None
```

### AdvancedReviewAnalyzer
```python
class AdvancedReviewAnalyzer:
    def analyze_sentiment_intensity() -> Dict
    def calculate_quality_score() -> Series  # 0-100
    def detect_issues() -> Dict[str, List[str]]
    def segment_players() -> Dict
    def analyze_temporal_trends() -> Dict
```

## API Endpoints

| Endpoint | Method | Parameters | Returns |
|----------|--------|-----------|---------|
| `/` | GET | — | Status |
| `/reviews` | GET | app_id*, language*, limit | List[Review] |
| `/reviews/{id}` | GET | — | Review |
| `/stats` | GET | app_id* | Stats |
| `/languages` | GET | app_id* | Dict |
| `/export/{format}` | GET | app_id*, format | File |

*optional parameter

## File Organization

```
src/steam_review/
├── storage/
│   └── database.py          ← ReviewDatabase class
├── dashboard/
│   ├── dashboard.py         ← Main Streamlit app
│   └── advanced_analytics_page.py
├── scraper/
│   └── steam_review_scraper.py
├── analysis/
│   ├── sentiment_analysis.py
│   ├── advanced_analyzer.py
│   ├── keyword_analysis.py
│   ├── topic_modeling.py
│   └── ... (14 modules total)
├── api/
│   └── api.py               ← FastAPI app
└── config.py                ← Configuration
```

## Key Data Transformations

### In Dashboard (load_data)
```python
# Raw: timestamp_created as Unix integer
# Converted: pd.to_datetime(df['timestamp_created'], unit='s')

# Playtime conversion
df['playtime_hours'] = df['playtime_forever'] / 60

# Binning
df['playtime_bin'] = pd.cut(df['playtime_hours'], 
                            bins=[0,1,5,10,20,50,100,200,500],
                            labels=['<1h', '1-5h', ...])

# Daily aggregation
daily = df.set_index('date').resample('D')['voted_up'].agg(['count', 'sum'])
daily['positive_rate'] = daily['sum'] / daily['count']
```

## Current Filters

### Dashboard Filters
- ✅ App ID (game selection)
- ✅ Limit (max review count)
- ❌ Sentiment range
- ❌ Date range
- ❌ Playtime range
- ❌ Text search

### Database Filters
- ✅ `app_id` (SQL WHERE)
- ✅ `limit` (SQL LIMIT)
- ❌ Sentiment (voted_up exists but not exposed)
- ❌ Language
- ❌ Timestamp range

## Important Locations

| What | Location |
|------|----------|
| Database | `/home/v/ai_apx/steam_review/data/reviews.db` |
| CSV Files | `/home/v/ai_apx/steam_review/data/*_reviews.csv` |
| Plots | `/home/v/ai_apx/steam_review/plots/*.png` |
| Config | `src/steam_review/config.py` |
| Dashboard Code | `src/steam_review/dashboard/dashboard.py` |
| Database Code | `src/steam_review/storage/database.py` |
| Analysis | `src/steam_review/analysis/` (14 modules) |

## Starting Points for Development

### To Add New Filter:
1. Edit `database.py` → `get_reviews()` method
2. Add new parameter and SQL WHERE clause
3. Update `dashboard.py` → sidebar UI
4. Update `api.py` → endpoint parameter
5. Add cache invalidation if needed

### To Add New Visualization:
1. Edit `dashboard.py` in appropriate page section
2. Use `load_data()` to fetch filtered data
3. Create Plotly figure with `px.*()` or `go.Figure()`
4. Use `st.plotly_chart()` to render

### To Add New Analysis:
1. Create module in `src/steam_review/analysis/`
2. Implement analysis function (takes DataFrame)
3. Generate plots with matplotlib/seaborn
4. Call from `full_analysis.py` → `generate_full_analysis()`

## Common Query Patterns

```python
# Get reviews for specific app
db = get_database()
df = db.get_reviews(app_id="2277560")

# Get all reviews with limit
df = db.get_reviews(limit=1000)

# Get stats for app
stats = db.get_stats(app_id="2277560")

# Insert new reviews
count = db.insert_reviews(df_new_reviews)

# Export data
db.export_to_csv("output.csv", app_id="2277560")
```

## Dependencies to Know

| Purpose | Package | Version |
|---------|---------|---------|
| Async HTTP | aiohttp | 3.12.15 |
| DataFrames | pandas | 2.3.1 |
| Sentiment | nltk | 3.9.1 |
| ML Models | transformers | 4.48.2 |
| Charts | plotly | 6.0.0 |
| Dashboard | streamlit | 1.42.2 |
| API | fastapi | 0.115.12 |
| Database | sqlite3 | built-in |
| NLP | jieba | 0.42.1 |

## Cache Strategy

- **TTL**: 5 minutes (300 seconds)
- **Scope**: Per Streamlit session
- **Decorator**: `@st.cache_data(ttl=300)`
- **Clear**: `st.cache_data.clear()` on data update

## Data Type Notes

- **Timestamps**: Stored as Unix epoch (int), converted to datetime[ns] on load
- **Booleans**: Stored as 0/1 (SQLite), converted on load from strings
- **Floats**: Coerced with errors='coerce' to handle missing values
- **Text**: UTF-8 encoded, handled with `astype(str)` conversions

