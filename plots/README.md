# Analysis Plots Directory

This directory contains **generated visualizations** from the Steam Review Analyzer and is **not tracked in version control**.

## Contents

This directory is populated with PNG images when you run:

1. **Dashboard**:
   ```bash
   streamlit run src/steam_review/dashboard/dashboard.py
   ```

2. **Analysis Script**:
   ```bash
   python -m steam_review.analysis.analyze_reviews <CSV_FILE>
   ```

## Generated Plot Types

### Overall Analysis (All Reviews)
- `sentiment_distribution.png` - Distribution of sentiment scores
- `sentiment_over_time.png` - Sentiment trends over time
- `sentiment_score_distribution.png` - Histogram of sentiment scores
- `overall_positive_keywords.png` - Top positive keywords
- `overall_negative_keywords.png` - Top negative keywords
- `overall_positive_wordcloud.png` - Word cloud of positive reviews
- `overall_negative_wordcloud.png` - Word cloud of negative reviews

### By Language
For each language (en, zh-cn, ja, ko, ru, es, fr, de, pt, etc.):
- `positive_keywords_{lang}.png` - Top positive keywords
- `negative_keywords_{lang}.png` - Top negative keywords
- `positive_wordcloud_{lang}.png` - Positive word cloud
- `negative_wordcloud_{lang}.png` - Negative word cloud

### Advanced Analysis
- `playtime_sentiment_boxplot.png` - Sentiment vs playtime
- `review_length_sentiment_boxplot.png` - Sentiment vs review length
- `sentiment_by_playtime.png` - Sentiment grouped by playtime
- `sentiment_by_review_length.png` - Sentiment grouped by review length
- `sentiment_by_early_access.png` - Early access vs standard release sentiment

### Game-Specific Plots
When analyzing specific games, plots are prefixed with the game name:
- `Game_Name_APPID_sentiment_by_playtime.png`
- `Game_Name_APPID_playtime_sentiment_boxplot.png`
- etc.

## Why Not in Git?

- **Large Binary Files**: PNG images don't compress well in git
- **User-Generated**: Different datasets produce different plots
- **Reproducibility**: Plots should be generated from current code
- **Repository Bloat**: Binary files inflate repository size

## Local Generation

### Quick Start
```bash
# 1. Scrape reviews
python -m steam_review.scraper.steam_review_scraper --app_id 2277560

# 2. Launch dashboard (auto-generates plots)
streamlit run src/steam_review/dashboard/dashboard.py

# Plots will be created in this directory
```

### From Python
```python
from steam_review.analysis.analyze_reviews import analyze_reviews

# This will generate all plots
analyze_reviews("game_reviews.csv", save_plots=True)
```

## Cleanup

To remove all plots:
```bash
# Clear the directory
rm -rf plots/*.png

# Recreate directory structure
mkdir -p plots
touch plots/.gitkeep

# Git will show "working tree clean"
```

## Storage Usage

All plots together typically use:
- **~50-100 MB** for a typical game with 5,000+ reviews
- **~500 MB+** for games with 50,000+ reviews
- **Varies** based on number of languages analyzed

Monitor disk usage:
```bash
du -sh plots/
```

## Docker Support

When using Docker, plots are persisted in a volume:
```bash
docker run -v steam-plots:/app/plots steam-review
```

---

**Note**: The `.gitkeep` file preserves this directory structure in git. Delete it after creating your first plots.
