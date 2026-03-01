# Steam Review Analytics - Documentation Index

## Overview

This project includes comprehensive documentation of the Steam Review Analyzer codebase. The documentation is organized into several focused documents for different purposes.

## Available Documentation

### 1. **CODEBASE_ANALYSIS.md** (21 KB)
**Comprehensive overview of the entire codebase**

This is the most detailed document covering:
- Complete project overview and tech stack
- **Database schema** - All 18 columns with descriptions
- **Dashboard architecture** - 6 pages, data loading, caching strategy
- **Database access patterns** - All query methods and parameters
- **Current filtering capabilities** - What's available and what's missing
- **Data pipeline** - Complete journey from scraping to visualization
- **Key data structures** - DataFrame columns and Pydantic models
- **Analysis modules** - All 14 analysis modules with descriptions
- **Project structure** - Complete file organization
- **Dependencies** - All libraries with versions
- **Key functions summary** - Database, Dashboard, Scraper, API methods
- **Limitations & gaps** - Current issues and missing features

**Best for**: Getting complete understanding of the system, development planning, feature additions

---

### 2. **QUICK_REFERENCE.md** (11 KB)
**Fast lookup guide for developers**

Perfect for quick reference:
- Database schema at a glance (table format)
- Data flow diagram (ASCII art)
- Core classes & methods (code snippets)
- API endpoints table
- File organization
- Key data transformations (code examples)
- Current filters (checkmarks for what exists)
- Important file locations
- Development starting points
- Common query patterns
- Dependencies table
- Cache strategy details
- Data type notes

**Best for**: Quick lookups while coding, remembering API endpoints, quick architecture overview

---

### 3. **DATABASE_AND_ARCHITECTURE.md** (21 KB)
**Deep dive into database design and data flow**

Detailed technical breakdown:
- **Complete schema** - Column definitions with types, nullability, indexes
- **SQL queries** - All 4 main query patterns with parameters
- **Data flow diagrams** - Detailed phase-by-phase flow (ASCII diagrams)
  - Phase 1: Scraping → Flattening → CSV
  - Phase 2: CSV → DataFrame → Cleaning → Database
  - Phase 3: Database → Query → Cleaning → Cache
  - Phase 4: Cache → Transformation → Visualization
- **Data type conversions** - JSON → CSV → SQLite → Pandas → Streamlit
- **Index strategy** - Why each index exists and performance impact
- **Deduplication strategy** - How duplicates are prevented
- **Type coercion** - How data is cleaned on load
- **Caching architecture** - TTL, invalidation, cache keys
- **Performance characteristics** - Complexity analysis for each operation
- **Storage estimates** - Per-review size and scaling calculations

**Best for**: Understanding database design, performance optimization, troubleshooting data issues

---

### 4. **README.md** (3.6 KB)
**Original project README**

- Installation instructions
- Basic usage commands
- Project features overview
- Quick start guide

**Best for**: Setting up and running the project for the first time

---

### 5. **ADVANCED_ANALYTICS.md** (2.3 KB)
**Advanced analysis features**

Details on advanced analysis capabilities (if present)

---

## Quick Navigation

### "I need to understand..."

| Topic | Document | Section |
|-------|----------|---------|
| Database schema | DATABASE_AND_ARCHITECTURE.md | Section 1 |
| How data flows | DATABASE_AND_ARCHITECTURE.md | Section 3 |
| All table columns | CODEBASE_ANALYSIS.md | Section 1 |
| Dashboard architecture | CODEBASE_ANALYSIS.md | Section 2 |
| How data is fetched | CODEBASE_ANALYSIS.md | Section 3 |
| Current filters | CODEBASE_ANALYSIS.md | Section 4 |
| All APIs | QUICK_REFERENCE.md | API Endpoints |
| Data types & conversions | DATABASE_AND_ARCHITECTURE.md | Section 4 |
| Index strategy | DATABASE_AND_ARCHITECTURE.md | Section 5 |
| Performance | DATABASE_AND_ARCHITECTURE.md | Section 10 |
| How to add a filter | QUICK_REFERENCE.md | Starting Points |
| File organization | CODEBASE_ANALYSIS.md | Section 8 |
| Dependencies | CODEBASE_ANALYSIS.md | Section 9 |

---

## Key Facts Summary

### Database
- **Type**: SQLite (reviews.db)
- **Tables**: 1 (reviews)
- **Columns**: 18
- **Indexes**: 3 (app_id, timestamp_created, voted_up)
- **Primary Key**: recommendation_id (TEXT)
- **Location**: `/home/v/ai_apx/steam_review/data/reviews.db`

### Dashboard
- **Framework**: Streamlit
- **Pages**: 6 (Overview, Scrape, Analysis, Advanced Analytics, Database, Settings)
- **Charts**: Plotly + Matplotlib + Seaborn
- **Cache**: 5-minute TTL, per-session
- **Port**: 8501

### API
- **Framework**: FastAPI
- **Endpoints**: 6 main endpoints
- **Port**: 8000
- **Authentication**: None (open)

### Data Pipeline
1. **Scraping**: Async aiohttp → Steam API
2. **Output**: CSV files (*_reviews.csv)
3. **Storage**: SQLite database (reviews.db)
4. **Analysis**: 14 specialized analysis modules
5. **Visualization**: Streamlit dashboard + FastAPI

### Analysis Capabilities
- **Sentiment**: VADER + BERT/RoBERTa
- **Keywords**: TF-IDF + frequency analysis
- **Topics**: LDA/NMF topic modeling
- **Trends**: Time series + prediction
- **Advanced**: Quality scoring, issue detection, player segmentation

### Current Filtering
- **Available**: App ID, limit, language (API only)
- **Missing**: Sentiment range, date range, playtime range, text search

---

## For Different Roles

### Software Developers
Start with: **QUICK_REFERENCE.md** → **CODEBASE_ANALYSIS.md** → **DATABASE_AND_ARCHITECTURE.md**

### Database Administrators
Start with: **DATABASE_AND_ARCHITECTURE.md** → **CODEBASE_ANALYSIS.md** (Section 3)

### Data Scientists
Start with: **CODEBASE_ANALYSIS.md** (Section 7) → **DATABASE_AND_ARCHITECTURE.md** (Data types)

### DevOps/Deployment
Start with: **README.md** → **QUICK_REFERENCE.md** (Important Locations)

### Product Managers
Start with: **CODEBASE_ANALYSIS.md** (Sections 4 & 11) → **QUICK_REFERENCE.md**

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Total Python files | 42 |
| Analysis modules | 14 |
| Database columns | 18 |
| Database indexes | 3 |
| API endpoints | 6 |
| Dashboard pages | 6 |
| Major dependencies | 15+ |
| Cache TTL | 300 seconds (5 min) |
| Approx per-review size | 1.7-2.2 KB |
| Max recommended reviews | 1-2 million |

---

## File Structure Reference

```
/home/v/ai_apx/steam_review/
├── src/steam_review/
│   ├── storage/database.py           ← Core DB class
│   ├── dashboard/dashboard.py        ← Main Streamlit app
│   ├── api/api.py                    ← FastAPI endpoints
│   ├── scraper/steam_review_scraper.py  ← Data collection
│   └── analysis/                     ← 14 analysis modules
├── data/
│   ├── reviews.db                    ← SQLite database
│   └── *_reviews.csv                 ← Scraped data
├── plots/                            ← Generated visualizations
└── [Documentation files]
    ├── CODEBASE_ANALYSIS.md          (This project's blueprint)
    ├── DATABASE_AND_ARCHITECTURE.md  (How data flows & stored)
    ├── QUICK_REFERENCE.md            (Cheat sheet)
    └── DOCUMENTATION_INDEX.md        (You are here)
```

---

## How to Use This Documentation

### For Reading Code
1. Check QUICK_REFERENCE.md for file locations
2. Read relevant section in CODEBASE_ANALYSIS.md for context
3. Check DATABASE_AND_ARCHITECTURE.md for data flow
4. Look at actual code with this context

### For Adding Features
1. Find what you want to add in QUICK_REFERENCE.md "Starting Points"
2. Check CODEBASE_ANALYSIS.md for existing implementations
3. Reference DATABASE_AND_ARCHITECTURE.md for data types
4. Use CODEBASE_ANALYSIS.md "Key Functions Summary" for API

### For Troubleshooting
1. Check "Current Limitations & Gaps" in CODEBASE_ANALYSIS.md
2. Look at data transformations in DATABASE_AND_ARCHITECTURE.md
3. Verify cache strategy in DATABASE_AND_ARCHITECTURE.md (Section 8)
4. Check dependencies in CODEBASE_ANALYSIS.md (Section 9)

---

## Last Updated
- Documentation Created: March 1, 2025
- Codebase Version: Current state as of project analysis
- Python Version: 3.12
- Key Dependency Versions: See CODEBASE_ANALYSIS.md Section 9

---

## Quick Links to Sections

**CODEBASE_ANALYSIS.md**:
- Section 1: Database schema
- Section 2: Dashboard architecture
- Section 3: Database queries
- Section 4: Filtering
- Section 5: Data pipeline
- Section 6: Data structures
- Section 7: Analysis modules
- Section 8: Project structure
- Section 9: Dependencies
- Section 10: Key functions
- Section 11: Limitations

**DATABASE_AND_ARCHITECTURE.md**:
- Section 1: Schema details
- Section 2: SQL queries
- Section 3: Data flow diagrams
- Section 4: Type conversions
- Section 5: Index strategy
- Section 6: Deduplication
- Section 7: Type coercion
- Section 8: Caching
- Section 9: Calculations
- Section 10: Performance
- Section 11: Storage

**QUICK_REFERENCE.md**:
- Schema at a glance
- Data flow diagram
- Core classes
- API endpoints
- File organization
- Data transformations
- Current filters
- Important locations
- Development guide
- Query patterns
- Dependencies
- Cache strategy

