# Steam Review Analyzer - Agent Coding Guide

## Quick Start

```bash
# Setup (Python 3.12 required)
uv venv .venv --python python3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
uv pip install -e ".[ml]"  # Optional: for ML features

# Run tests
python -m pytest src/tests/ -v

# Run single test file
python -m pytest src/tests/test_config.py -v

# Run single test
python -m pytest src/tests/test_config.py::TestConfig::test_get_game_name_known_app -v

# Lint
ruff check src/ --select=E,F,W
black src/
mypy src/steam_review --ignore-missing-imports

# Type check single file
mypy src/steam_review/config.py --ignore-missing-imports

# Run CLI
steam-review --help
steam-review scrape -a 2277560 -l 100
steam-review stats
streamlit run src/steam_review/dashboard/dashboard.py
```

## Project Structure

```
src/steam_review/
├── __init__.py          # DO NOT add sys.path here manually - use package imports
├── config.py            # Central config (paths, GAME_NAMES, SCRAPER_CONFIG)
├── cli/cli.py           # Click CLI (steam-review command)
├── scraper/            # Steam API scraping
├── storage/            # SQLite database operations
├── analysis/           # NLP, sentiment analysis
├── dashboard/          # Streamlit UI
├── api/                # FastAPI endpoints
└── utils/              # Helpers
```

## Code Style

### Imports (IMPORTANT)
```python
# ✅ CORRECT - Use package imports
from src.steam_review.storage.database import get_database
from src.steam_review import config
from src.steam_review.scraper.steam_review_scraper import flatten_review

# ❌ WRONG - Never manually add sys.path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### Formatting
- Line length: 100 characters
- Use Black for formatting: `black src/`
- Use isort for imports: `isort src/`
- Configuration in `pyproject.toml`

### Type Annotations
- Use Python 3.12 syntax (no `from __future__ import annotations`)
- Add return types to all public functions
```python
def get_game_name(app_id: str | None) -> str:
    ...
```

### Naming Conventions
- Modules/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_private_method(self)`

### Error Handling
- Use specific exception types
- Add logging for errors
- Network requests need retry logic
```python
try:
    async with session.get(url) as response:
        response.raise_for_status()
except aiohttp.ClientResponseError as e:
    if e.status == 429:
        # Handle rate limit
    else:
        logging.warning(f"Request failed: {e}")
```

## Testing

### Test File Location
```
src/tests/
├── test_database.py
├── test_config.py
├── test_cli.py
├── test_scraper.py
└── test_analyze_reviews.py
```

### Test Conventions
- Use pytest fixtures with `tmp_path` for file operations
- Mock external dependencies (network, filesystem)
- Async tests: use `@pytest.mark.asyncio`
- Test class: `Test<ClassName>`, test methods: `test_*`

```python
@pytest.fixture
def temp_db(self, tmp_path):
    db_path = tmp_path / "test.db"
    yield ReviewDatabase(db_path=str(db_path))
    # Cleanup handled by tmp_path

@pytest.mark.asyncio
async def test_get_reviews(self, mock_session):
    ...
```

## Common Issues

1. **Import errors**: Ensure `.venv` is activated
2. **Database locked**: Use aiosqlite or close connections
3. **Python 3.14**: Not supported - use Python 3.12
4. **Steam API 429**: Scraper has built-in retry logic

## Key Modules

| Module | Key Functions |
|--------|---------------|
| `config.py` | `get_game_name()`, `GAME_NAMES`, `SCRAPER_CONFIG` |
| `database.py` | `get_database()`, `insert_reviews()`, `get_all_games()` |
| `cli.py` | `scrape`, `stats`, `analyze`, `dashboard` commands |
| `scraper/` | `get_reviews()`, `flatten_review()`, checkpointing |

## Dependencies

- **Core**: `uv pip install -e ".[dev]"`
- **ML (optional)**: `uv pip install -e ".[ml]"` for transformers/torch

## CI/CD

GitHub Actions (`.github/workflows/`):
- Tests on Python 3.10, 3.11, 3.12
- Ruff linting
- mypy type checking
- Security scans (bandit, safety)

Run locally: `ruff check src/` and `mypy src/steam_review --ignore-missing-imports`
