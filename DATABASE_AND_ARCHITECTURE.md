# Database Schema & Architecture Deep Dive

## 1. Complete Database Schema

### Table: `reviews`

**Location**: `/home/v/ai_apx/steam_review/data/reviews.db`

**Creation Statement** (from database.py line 24-44):
```sql
CREATE TABLE IF NOT EXISTS reviews (
    recommendation_id TEXT PRIMARY KEY,
    app_id TEXT,
    language TEXT,
    review TEXT,
    timestamp_created INTEGER,
    timestamp_updated INTEGER,
    voted_up INTEGER,
    playtime_forever REAL,
    playtime_last_two_weeks REAL,
    author_steam_id TEXT,
    author_num_games_owned INTEGER,
    author_num_reviews INTEGER,
    author_playtime_forever REAL,
    written_during_early_access INTEGER,
    detected_language TEXT,
    sentiment_score REAL,
    review_length INTEGER,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Indexes

```sql
CREATE INDEX idx_app_id ON reviews(app_id)
CREATE INDEX idx_timestamp ON reviews(timestamp_created)
CREATE INDEX idx_voted_up ON reviews(voted_up)
```

### Column Details with Examples

| # | Column | Type | Nullable | Indexed | Example Value | Notes |
|---|--------|------|----------|---------|---------------|-------|
| 1 | `recommendation_id` | TEXT | NO | YES (PK) | "12345678901234567" | Steam review ID, unique identifier |
| 2 | `app_id` | TEXT | YES | YES | "2277560" | Steam app ID, can be string or int |
| 3 | `language` | TEXT | YES | NO | "english" | Review language from Steam |
| 4 | `review` | TEXT | YES | NO | "Great game, loved it!" | Full review text (UTF-8) |
| 5 | `timestamp_created` | INTEGER | YES | YES | 1704067200 | Unix epoch (seconds since 1970) |
| 6 | `timestamp_updated` | INTEGER | YES | NO | 1704153600 | When review was last edited |
| 7 | `voted_up` | INTEGER | YES | YES | 1 | Boolean: 1=positive, 0=negative |
| 8 | `playtime_forever` | REAL | YES | NO | 1200.5 | Total playtime in minutes |
| 9 | `playtime_last_two_weeks` | REAL | YES | NO | 120.0 | Recent playtime in minutes |
| 10 | `author_steam_id` | TEXT | YES | NO | "76561198123456789" | Steam ID of reviewer |
| 11 | `author_num_games_owned` | INTEGER | YES | NO | 250 | Author's game library size |
| 12 | `author_num_reviews` | INTEGER | YES | NO | 42 | Author's total reviews written |
| 13 | `author_playtime_forever` | REAL | YES | NO | 5600.0 | Author's total playtime (minutes) |
| 14 | `written_during_early_access` | INTEGER | YES | NO | 0 | Boolean: 1=written during EA |
| 15 | `detected_language` | TEXT | YES | NO | "en" | Language detected by langdetect |
| 16 | `sentiment_score` | REAL | YES | NO | 0.75 | VADER sentiment (-1 to 1) |
| 17 | `review_length` | INTEGER | YES | NO | 450 | Character count of review text |
| 18 | `scraped_at` | TIMESTAMP | YES | NO | "2025-03-01 10:30:00" | When added to database |

## 2. Common SQL Queries Used in Codebase

### Query 1: Get All Reviews (database.py:100-107)
```sql
SELECT * FROM reviews
WHERE app_id = ? 
ORDER BY timestamp_created DESC
LIMIT ?
```
**Parameters**: app_id (optional), limit (optional)
**Returns**: All columns, newest first

### Query 2: Get Statistics (database.py:139-143)
```sql
SELECT COUNT(*) as total, SUM(voted_up) as positive
FROM reviews
WHERE app_id = ?
```
**Calculates**:
- `total` = COUNT(*)
- `positive` = SUM(voted_up) [sum of 1s]
- `negative` = total - positive [derived]

### Query 3: Get Existing IDs (database.py:89)
```sql
SELECT recommendation_id FROM reviews
```
**Purpose**: Deduplication check before insert

### Query 4: Get Table Schema (database.py:96)
```sql
PRAGMA table_info(reviews)
```
**Returns**: Column metadata for validation

## 3. Data Flow Diagram - Detailed

### Phase 1: Scraping (steam_review_scraper.py)

```
┌─────────────────────────────────────────────────┐
│              STEAM API RESPONSE                 │
│  {                                              │
│    "success": 1,                                │
│    "reviews": [                                 │
│      {                                          │
│        "recommendationid": "12345...",          │
│        "author": {                              │
│          "steamid": "7656...",                  │
│          "num_games_owned": 250,                │
│          "num_reviews": 42,                     │
│          "playtime_forever": 5600               │
│        },                                       │
│        "language": "english",                   │
│        "review": "Text...",                     │
│        "timestamp_created": 1704067200,         │
│        "voted_up": true                         │
│      }                                          │
│    ],                                           │
│    "cursor": "next_page_cursor"                 │
│  }                                              │
└────────┬────────────────────────────────────────┘
         │ flatten_review()
         ▼
┌─────────────────────────────────────────────────┐
│         FLATTENED REVIEW STRUCTURE              │
│  {                                              │
│    "recommendationid": "12345...",              │ 
│    "author.steamid": "7656...",                 │ ← Flattened
│    "author.num_games_owned": 250,               │ ← Flattened
│    "author.num_reviews": 42,                    │ ← Flattened
│    "author.playtime_forever": 5600,             │ ← Flattened
│    "language": "english",                       │
│    "review": "Text...",                         │
│    "timestamp_created": 1704067200,             │
│    "voted_up": true                             │
│  }                                              │
└────────┬────────────────────────────────────────┘
         │ CSV Write
         ▼
┌─────────────────────────────────────────────────┐
│         CSV FILE (*_reviews.csv)                │
│  recommendation_id,author.steamid,language,...  │
│  12345...,7656...,english,...                   │
│  67890...,1234...,chinese,...                   │
└─────────────────────────────────────────────────┘
```

### Phase 2: CSV to Database (database.py:51-84)

```
┌──────────────────────────┐
│   CSV FILE (Raw)         │
│  (various column names)  │
│  (mixed types)           │
│  (possible duplicates)   │
└────────┬─────────────────┘
         │ pd.read_csv()
         ▼
┌──────────────────────────────────────────┐
│     DataFrame (Pre-process)              │
│  recommendation_id (some missing?)       │
│  app_id or appid (inconsistent naming)   │
│  Duplicate column names                  │
└────────┬─────────────────────────────────┘
         │ Normalization
         │ 1. Rename columns
         │ 2. Load existing IDs
         │ 3. Filter duplicates
         ▼
┌──────────────────────────────────────────┐
│     DataFrame (Cleaned)                  │
│  Only new review IDs                     │
│  Consistent column names                 │
│  Valid for DB schema                     │
└────────┬─────────────────────────────────┘
         │ SQLite INSERT
         ▼
┌──────────────────────────────────────────┐
│      SQLite reviews TABLE                │
│  19 columns, 3 indexes                   │
│  Type conversions applied                │
└──────────────────────────────────────────┘
```

### Phase 3: Dashboard Data Loading (dashboard.py:52-61)

```
┌──────────────────────────────────────────┐
│        Database Query Execution          │
│  get_reviews(app_id="2277560", limit=5000)
└────────┬─────────────────────────────────┘
         │ SQL Query
         │ SELECT * FROM reviews
         │ WHERE app_id = '2277560'
         │ ORDER BY timestamp_created DESC
         │ LIMIT 5000
         ▼
┌──────────────────────────────────────────┐
│   DataFrame (Raw from DB)                │
│  - timestamp_created: int (Unix epoch)   │
│  - voted_up: may be string ('True'/'0')  │
│  - NaN values in some columns            │
│  - Streamlit Arrow incompatibility       │
└────────┬─────────────────────────────────┘
         │ Data Cleaning (get_reviews)
         │ 1. Convert timestamps
         │ 2. Fix boolean strings
         │ 3. Drop all-NaN columns
         ▼
┌──────────────────────────────────────────┐
│   DataFrame (Cleaned)                    │
│  - timestamp_created: datetime64[ns]     │
│  - voted_up: int (1/0)                   │
│  - Arrow compatible                      │
└────────┬─────────────────────────────────┘
         │ @st.cache_data(ttl=300)
         │ (Cache for 5 minutes)
         ▼
┌──────────────────────────────────────────┐
│   Streamlit Memory Cache                 │
│  Session-scoped, 5-minute TTL            │
└──────────────────────────────────────────┘
```

### Phase 4: Transformation for Visualization

```
┌──────────────────────────────────────────┐
│   Cached DataFrame                       │
│  timestamp_created: datetime64[ns]       │
│  playtime_forever: float                 │
│  voted_up: int                           │
│  review: str                             │
└────────┬─────────────────────────────────┘
         │ Transformation for Charts
         ├─ Extract date: pd.to_datetime()
         ├─ Convert units: /60 for hours
         ├─ Bin continuous: pd.cut()
         ├─ Aggregate: resample('D')
         ▼
┌──────────────────────────────────────────┐
│   Enhanced DataFrame                     │
│  date: datetime64[ns]        (NEW)       │
│  playtime_hours: float       (NEW)       │
│  playtime_bin: category      (NEW)       │
│  positive_rate: float        (NEW)       │
│  (all original columns)                  │
└────────┬─────────────────────────────────┘
         │ Plotly Visualization
         │ px.bar(), px.line(), go.Pie()
         ▼
┌──────────────────────────────────────────┐
│   Interactive Charts                     │
│  Rendered in Streamlit                   │
│  Hover details, zoom, export to PNG      │
└──────────────────────────────────────────┘
```

## 4. Data Type Conversions

### When Data Enters Database (Scraper → Database)

```
Steam API JSON          →    CSV Format          →    SQLite Storage
────────────────────────────────────────────────────────────────────
string                  →    text (quoted)       →    TEXT
int                     →    number              →    INTEGER
float                   →    number              →    REAL
bool (true/false)       →    true/False/1/0      →    INTEGER (0/1)
null                    →    empty/missing       →    NULL
timestamp (int)         →    number              →    INTEGER
nested object           →    flattened key       →    TEXT/REAL
array                   →    serialized          →    TEXT
```

### When Data Leaves Database (Database → Dashboard)

```
SQLite Type  →    Pandas Type     →    After Cleaning     →    Streamlit Type
──────────────────────────────────────────────────────────────────────────────
TEXT         →    object (str)    →    object (str)       →    st.write()
INTEGER      →    int64           →    int64              →    st.metric()
REAL         →    float64         →    float64            →    st.metric()
NULL         →    NaN             →    dropped (columns)  →    (not rendered)
────────────────────────────────────────────────────────────────────────────

Special Cases:
- timestamp_created: INTEGER → float64 → datetime64[ns] (via pd.to_datetime)
- voted_up: INTEGER but sometimes STRING ('True'/'False') → int (via .map())
- playtime fields: REAL → float64 → float64/60 (for hours)
```

## 5. Index Strategy

### Why These Indexes?

```
Index              Column               Reason
──────────────────────────────────────────────────────────────
idx_app_id         app_id               Frequent WHERE filtering by game
                                        Dashboard sidebar filter
                                        API /reviews?app_id=X

idx_timestamp      timestamp_created    Time-series charting
                                        ORDER BY timestamp_created DESC
                                        Sorting reviews by date

idx_voted_up       voted_up             Sentiment distribution calculations
                                        SUM(voted_up) aggregations
                                        Filtering positive/negative
```

### Query Optimization Impact

```
Without Indexes:
  SELECT * FROM reviews WHERE app_id = '2277560'
  → Full table scan: O(n)

With idx_app_id:
  SELECT * FROM reviews WHERE app_id = '2277560'
  → Index lookup: O(log n)

Time-Series Queries:
  ORDER BY timestamp_created DESC LIMIT 1000
  → Uses idx_timestamp for fast sorting
```

## 6. Deduplication Strategy

### The Problem
- Scraper can be re-run on same game
- Steam API might return same reviews
- Need to avoid duplicates in database

### The Solution (database.py:69-72)

```python
# Step 1: Get existing IDs from database
existing_ids = self.get_existing_ids()  # Set of strings

# Step 2: Load new reviews from CSV
df['recommendation_id'] = df['recommendation_id'].astype(str)

# Step 3: Filter to only NEW reviews
new_reviews = df[~df['recommendation_id'].isin(existing_ids)]

# Step 4: Insert only new reviews
new_reviews[columns].to_sql('reviews', conn, if_exists='append', index=False)
```

**Complexity**: O(n) where n = number of new reviews (set membership is O(1))

## 7. Type Coercion on Load

### Problem
CSV files may have type mismatches:
- "True"/"False" as strings instead of 1/0
- "123" as string instead of int
- Mixed int/float/null in numeric columns

### Solution (database.py:113-134)

```python
# Convert timestamp columns
for col in ['timestamp_created', 'timestamp_updated']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
    # errors='coerce' → NaN for unparseable values

# Convert boolean columns from strings
for col in ['voted_up', 'is_recommended']:
    if df[col].dtype == 'object':  # Is string
        df[col] = df[col].map({
            'True': 1, 'False': 0,
            '1': 1, '0': 0,
            True: 1, False: 0
        })
        df[col] = df[col].fillna(0).astype(int)

# Drop columns with all NaN (Arrow compatibility)
df = df.dropna(axis=1, how='all')
```

## 8. Caching Architecture

### Streamlit Cache with TTL

```python
@st.cache_data(ttl=300)  # 5 minutes
def load_data(app_id=None, limit=5000):
    db = get_database()
    df = db.get_reviews(app_id, limit)
    # ... transformations ...
    return df
```

**Caching Flow**:
```
First Call: load_data(app_id='2277560')
└─ Database query executed
└─ DataFrame returned
└─ Stored in cache with TTL=300s
└─ Cache key = (app_id='2277560')

Second Call (within 5 min): load_data(app_id='2277560')
└─ Cache hit!
└─ Return cached DataFrame without DB query

Third Call (after 5 min): load_data(app_id='2277560')
└─ Cache expired
└─ Database query executed again

Different Call: load_data(app_id='3363270')
└─ Different cache key
└─ Cache miss
└─ Database query executed
```

### Cache Invalidation

Manual invalidation in dashboard.py:
```python
# Line 164
st.cache_data.clear()  # After running analysis

# Line 389
st.cache_data.clear()  # After scraping new data
```

## 9. Review Count Calculation

### SQL Aggregation (database.py:139-151)

```sql
SELECT COUNT(*) as total, SUM(voted_up) as positive
FROM reviews
WHERE app_id = '2277560'
```

**Result Interpretation**:
```
If votes: 1,0,1,1,0,1
├─ COUNT(*) = 6 (total reviews)
├─ SUM(voted_up) = 4 (sum of 1's = positive count)
└─ Calculated: negative = 6 - 4 = 2

Stats returned:
{
    'total': 6,
    'positive': 4,
    'negative': 2
}
```

## 10. Performance Characteristics

### Read Operations
```
Operation                    Complexity    Notes
──────────────────────────────────────────────────
get_reviews(limit=5000)     O(n log n)    Index lookup + sort
get_reviews(app_id=X)       O(log n)      Index lookup, then linear read
get_stats(app_id=X)         O(n)          Full scan of app_id index
get_existing_ids()          O(n)          Full table scan
```

### Write Operations
```
Operation                    Complexity    Notes
──────────────────────────────────────────────────
insert_reviews (k new)      O(k + n)      Scan existing (n) + insert (k)
```

## 11. Storage Estimate

### Per Review (Approximate)
```
Column                          Size
─────────────────────────────────────
recommendation_id (TEXT)        17 bytes
app_id (TEXT)                   4 bytes
language (TEXT)                 8 bytes
review (TEXT)                   500-2000 bytes (avg 1000)
timestamp_created (INTEGER)     8 bytes
timestamp_updated (INTEGER)     8 bytes
voted_up (INTEGER)              1 byte
playtime_forever (REAL)         8 bytes
playtime_last_two_weeks (REAL)  8 bytes
author_steam_id (TEXT)          17 bytes
author_num_games_owned (INT)    4 bytes
author_num_reviews (INT)        4 bytes
author_playtime_forever (REAL)  8 bytes
written_during_early_access (INT) 1 byte
detected_language (TEXT)        2 bytes
sentiment_score (REAL)          8 bytes
review_length (INTEGER)         4 bytes
scraped_at (TIMESTAMP)          8 bytes
────────────────────────────────────
Total per review: ~1.7-2.2 KB

For 10,000 reviews: 17-22 MB
For 100,000 reviews: 170-220 MB
For 1,000,000 reviews: 1.7-2.2 GB
```

