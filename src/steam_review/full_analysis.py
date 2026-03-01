#!/usr/bin/env python3
import sys
import os

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import argparse
import logging

from src.steam_review import config
from src.steam_review.analysis import sentiment_analysis
from src.steam_review.analysis import keyword_analysis
from src.steam_review.analysis import correlation_analysis
from src.steam_review.analysis import time_series_analysis
from src.steam_review.analysis import advanced_sentiment
from src.steam_review.analysis import topic_modeling
from src.steam_review.analysis import trend_prediction
from src.steam_review.storage.database import get_database

config.setup_logging()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 100

PLOTS_DIR = 'plots'


def create_dashboard(df, app_name, output_path='dashboard.html'):
    # Reset index to access timestamp_created
    df_reset = df.reset_index()
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name} - Review Analysis Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); flex: 1; min-width: 150px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #3498db; }}
        .stat-label {{ color: #7f8c8d; margin-top: 5px; }}
        .positive {{ color: #27ae60; }}
        .negative {{ color: #e74c3c; }}
        .chart {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin: 20px 0; }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }}
        .footer {{ text-align: center; margin-top: 40px; color: #95a5a6; }}
        @media (max-width: 768px) {{ .grid-2, .grid-3 {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 {app_name} - Steam Review Analysis</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(df)}</div>
                <div class="stat-label">Total Reviews</div>
            </div>
            <div class="stat-card">
                <div class="stat-value positive">{int(df['voted_up'].sum())}</div>
                <div class="stat-label">Positive Reviews</div>
            </div>
            <div class="stat-card">
                <div class="stat-value negative">{int((~df['voted_up']).sum())}</div>
                <div class="stat-label">Negative Reviews</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{df['voted_up'].mean()*100:.1f}%</div>
                <div class="stat-label">Positive Rate</div>
            </div>
        </div>
        
        <h2>📊 Sentiment Overview</h2>
        <div class="grid-2">
            <div class="chart">
                <div id="sentiment-pie"></div>
            </div>
            <div class="chart">
                <div id="language-dist"></div>
            </div>
        </div>
        
        <h2>📈 Time Trends</h2>
        <div class="chart">
            <div id="time-trend"></div>
        </div>
        
        <h2>🔍 Review Analysis</h2>
        <div class="grid-2">
            <div class="chart">
                <div id="playtime-dist"></div>
            </div>
            <div class="chart">
                <div id="length-dist"></div>
            </div>
        </div>
        
        <h2>⭐ Rating Distribution</h2>
        <div class="chart">
            <div id="rating-dist"></div>
        </div>
        
        <div class="footer">
            <p>Steam Review Analyzer - Generated with ❤️</p>
        </div>
    </div>
    
    <script>
        // Sentiment Pie Chart
        var sentimentData = [{{
            values: [{int(df['voted_up'].sum())}, {int((~df['voted_up']).sum())}],
            labels: ['Positive', 'Negative'],
            type: 'pie',
            marker: {{ colors: ['#27ae60', '#e74c3c'] }},
            hole: 0.4
        }};
        Plotly.newPlot('sentiment-pie', sentimentData, {{title: 'Sentiment Distribution', font: {{size: 14}}}});
        
        // Language Distribution
        var langCounts = {df_reset['language'].value_counts().head(10).to_dict()};
        var langData = [{{
            x: Object.keys(langCounts),
            y: Object.values(langCounts),
            type: 'bar',
            marker: {{ color: '#3498db' }}
        }}];
        Plotly.newPlot('language-dist', langData, {{title: 'Top 10 Languages', font: {{size: 14}}}});
        
        // Time Trend
        var dates = {df_reset.sort_values('timestamp_created').tail(100)['timestamp_created'].astype(str).tolist()};
        var votes = {df_reset.sort_values('timestamp_created').tail(100)['voted_up'].astype(int).tolist()};
        var trendData = [{{
            x: dates,
            y: votes,
            type: 'scatter',
            mode: 'lines+markers',
            line: {{ color: '#9b59b6' }}
        }}];
        Plotly.newPlot('time-trend', trendData, {{title: 'Recent Reviews Trend', font: {{size: 14}}}});
        
        // Playtime Distribution
        var playtime = {df['playtime_hours'].dropna().clip(0, 500).tolist()};
        var histData = [{{
            x: playtime,
            type: 'histogram',
            marker: {{ color: '#1abc9c' }}
        }}];
        Plotly.newPlot('playtime-dist', histData, {{title: 'Playtime Distribution (hours)', font: {{size: 14}}}});
        
        // Review Length Distribution
        var lengths = {df['review'].astype(str).str.len().clip(0, 2000).tolist()};
        var lengthData = [{{
            x: lengths,
            type: 'histogram',
            marker: {{ color: '#f39c12' }}
        }}];
        Plotly.newPlot('length-dist', lengthData, {{title: 'Review Length Distribution', font: {{size: 14}}}});
        
        // Rating Distribution
        var voteScores = {df.get('weighted_vote_score', pd.Series([0]*len(df))).dropna().mul(5).round().tolist()};
        var ratingData = [{{
            x: voteScores,
            type: 'histogram',
            marker: {{ color: '#e74c3c' }},
            nbinsx: 5
        }}];
        Plotly.newPlot('rating-dist', ratingData, {{title: 'Rating Distribution (1-5 stars)', font: {{size: 14}}}});
    </script>
</body>
</html>"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Dashboard saved to: {output_path}")


def generate_full_analysis(csv_file, output_dir='plots'):
    print(f"\n{'='*60}")
    print(f"Starting comprehensive review analysis")
    print(f"{'='*60}\n")
    
    if not os.path.exists(csv_file):
        print(f"Error: File {csv_file} not found")
        return
    
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} reviews")
    
    app_name = os.path.basename(csv_file).split('_reviews')[0]
    
    # Prepare data
    df['timestamp_created'] = pd.to_datetime(df['timestamp_created'], unit='s', errors='coerce')
    df = df.set_index('timestamp_created')
    df['review_length'] = df['review'].astype(str).str.len()
    playtime_col = df.get('author.playtime_forever', pd.Series([0]*len(df), index=df.index))
    if playtime_col.dtype == 'object':
        playtime_col = pd.to_numeric(playtime_col, errors='coerce').fillna(0)
    df['playtime_hours'] = playtime_col / 60
    
    # Add detected_language if not present
    if 'detected_language' not in df.columns:
        print("\n[0/6] Detecting languages...")
        from langdetect import detect, LangDetectException
        from langdetect.detector_factory import DetectorFactory
        DetectorFactory.seed = 0
        
        def detect_lang(text):
            try:
                return detect(str(text)[:100])
            except:
                return 'unknown'
        
        df['detected_language'] = df['review'].apply(detect_lang)
    
    # Run analyses
    print("\n[1/6] Running sentiment analysis...")
    sentiment_analysis.analyze_sentiment(df)
    
    print("[2/5] Running keyword analysis...")
    keyword_analysis.analyze_keywords(df)
    
    print("[3/5] Running correlation analysis...")
    correlation_analysis.analyze_correlation(df, app_name)
    
    print("[4/5] Running time series analysis...")
    time_series_analysis.analyze_time_series(df)
    
    print("[5/5] Generating interactive dashboard...")
    dashboard_path = f"{app_name}_dashboard.html"
    create_dashboard(df, app_name, dashboard_path)
    
    print(f"\n{'='*60}")
    print(f"Analysis complete!")
    print(f"{'='*60}")
    print(f"\nGenerated files:")
    print(f"  - Dashboard: {dashboard_path}")
    print(f"  - Plots: {output_dir}/")
    print(f"\nTo view the dashboard, open {dashboard_path} in a web browser")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate comprehensive review analysis")
    parser.add_argument("csv_file", nargs='?', default="Fischer_s Fishing Journey_3363270_reviews.csv",
                        help="CSV file to analyze")
    parser.add_argument("--output", "-o", default="plots", help="Output directory")
    
    args = parser.parse_args()
    generate_full_analysis(args.csv_file, args.output)
