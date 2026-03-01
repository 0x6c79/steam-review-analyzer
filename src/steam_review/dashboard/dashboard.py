#!/usr/bin/env python3
"""
Steam Review Analytics Dashboard - Streamlit Web Interface
"""
import os
import sys

# Get project root - use config instead of chdir
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Add project root to path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.steam_review.storage.database import get_database
from src.steam_review import config as app_config
from src.steam_review.dashboard.advanced_analytics_page import render_advanced_analytics
import asyncio

app_config.setup_logging()

st.set_page_config(
    page_title="Steam Review Analytics",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; }
    .stat-card { 
        background-color: white; 
        padding: 20px; 
        border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .positive { color: #27ae60; }
    .negative { color: #e74c3c; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_data(app_id=None, limit=5000):
    db = get_database()
    df = db.get_reviews(app_id, limit)
    # Fix timestamp parsing
    if 'timestamp_created' in df.columns:
        try:
            df['timestamp_created'] = pd.to_datetime(df['timestamp_created'], unit='s', errors='coerce')
        except:
            df['timestamp_created'] = pd.to_datetime(df['timestamp_created'], errors='coerce')
    return df


@st.cache_data(ttl=300)
def load_stats(app_id=None):
    db = get_database()
    return db.get_stats(app_id)


def get_csv_files():
    data_dir = os.path.join(PROJECT_ROOT, 'data')
    files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('_reviews.csv')]
    files = sorted(files, key=os.path.getmtime, reverse=True)
    return [os.path.basename(f) for f in files]


def run_scrape(app_id, limit):
    from src.steam_review.scraper.steam_review_scraper import main as scrape_main
    import asyncio
    result = asyncio.run(scrape_main(str(app_id), limit, False))
    return result


def run_analyze(csv_file, save_db):
    from src.steam_review.full_analysis import generate_full_analysis
    generate_full_analysis(csv_file, 'plots')


# Sidebar
with st.sidebar:
    st.title("🎮 Steam Review")
    
    # App selection
    db = get_database()
    df_all = db.get_reviews()
    
    from src.steam_review import config
    
    if not df_all.empty and 'app_id' in df_all.columns:
        # Filter out None values and get unique app IDs
        app_ids_list = [str(aid) for aid in df_all['app_id'].unique().tolist() if aid is not None]
        # Create display names (Game Name - App ID)
        app_options = ["All"] + sorted([
            f"{config.get_game_name(aid)} ({aid})" for aid in app_ids_list
        ])
        # Store mapping for later use
        app_id_map = {f"{config.get_game_name(aid)} ({aid})": aid for aid in app_ids_list}
    else:
        app_options = ["All"]
        app_id_map = {}
    
    selected_app_display = st.selectbox("Select Game", app_options)
    # Extract app_id from selection
    if selected_app_display == "All":
        app_id_filter = None
    else:
        app_id_filter = app_id_map.get(selected_app_display)
    
    st.divider()
    
    # Navigation
    st.subheader("📁 Navigation")
    page = st.radio("Go to", ["📊 Overview", "🔍 Scrape", "📈 Analysis", "🔬 Advanced Analytics", "💾 Database", "⚙️ Settings"])
    
    st.divider()
    
    # Quick stats
    st.subheader("📈 Quick Stats")
    stats = load_stats(app_id_filter)
    if stats['total'] > 0:
        st.metric("Total Reviews", stats['total'])
        st.metric("Positive Rate", f"{stats['positive']/stats['total']*100:.1f}%")
    else:
        st.info("No data available")


# Main content
if page == "📊 Overview":
    st.title("📊 Steam Review Analytics Dashboard")
    
    stats = load_stats(app_id_filter)
    df = load_data(app_id_filter, 5000)
    
    if df.empty:
        st.warning("No data available. Go to 🔍 Scrape to fetch reviews.")
        st.stop()
    
    # Optimized startup - skip analysis if cached
    from src.steam_review.dashboard.startup_optimizer import (
        get_startup_optimizer, DashboardStartupConfig
    )
    
    optimizer = get_startup_optimizer(enable_cache=True)
    startup_config = DashboardStartupConfig()
    
    csv_file = None
    csv_files = get_csv_files()
    if csv_files:
        csv_file = os.path.join(PROJECT_ROOT, 'data', csv_files[0])
        plots_dir = os.path.join(PROJECT_ROOT, 'plots')
        
        # Check if analysis is needed
        if optimizer.should_run_analysis(csv_file, plots_dir, force=False):
            if startup_config.auto_analysis_enabled:
                with st.spinner("Running initial analysis..."):
                    try:
                        from src.steam_review.full_analysis import generate_full_analysis
                        generate_full_analysis(csv_file, plots_dir)
                        optimizer.record_successful_analysis(csv_file, plots_dir)
                        st.cache_data.clear()
                    except Exception as e:
                        st.warning(f"Auto-analysis skipped: {e}")
            else:
                # Analysis not found, show user option
                st.info("""
                📊 **Analysis plots not yet generated**
                
                Click the button below to generate detailed analysis charts for better insights.
                This will be cached for future sessions.
                """)
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("🔄 Generate Analysis", use_container_width=True):
                        with st.spinner("Generating analysis plots..."):
                            try:
                                from src.steam_review.full_analysis import generate_full_analysis
                                generate_full_analysis(csv_file, plots_dir)
                                optimizer.record_successful_analysis(csv_file, plots_dir)
                                st.cache_data.clear()
                                st.success("✅ Analysis complete!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Analysis failed: {e}")
        else:
            if startup_config.show_startup_info:
                st.success("✅ Using cached analysis from previous session")
    
    # ========== Stats Row ==========
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Reviews", f"{stats['total']:,}")
    with col2:
        st.metric("Positive", f"{stats['positive']:,}", delta_color="normal")
    with col3:
        st.metric("Negative", f"{stats['negative']:,}", delta_color="inverse")
    with col4:
        rate = stats['positive']/stats['total']*100 if stats['total'] > 0 else 0
        st.metric("Positive Rate", f"{rate:.1f}%")
    
    st.divider()
    
    # ========== Row 1: Sentiment & Language ==========
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("😊 Sentiment Distribution")
        fig = go.Figure(data=[go.Pie(
            labels=['Positive', 'Negative'],
            values=[stats['positive'], stats['negative']],
            marker=dict(colors=['#27ae60', '#e74c3c']),
            hole=0.4,
            textinfo='percent',
            hoverinfo='label+value+percent'
        )])
        fig.update_layout(showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🌐 Language Distribution")
        if 'language' in df.columns:
            lang_counts = df['language'].value_counts().head(10).reset_index()
            lang_counts.columns = ['Language', 'Count']
            fig = px.bar(
                lang_counts,
                x='Count', 
                y='Language', 
                orientation='h',
                labels={'x': 'Count', 'y': 'Language'},
                color='Count', 
                color_continuous_scale='viridis'
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # ========== Row 2: Time Series & Sentiment Over Time ==========
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Reviews Over Time")
        if 'timestamp_created' in df.columns:
            df_copy = df.copy()
            df_copy['date'] = pd.to_datetime(df_copy['timestamp_created'], unit='s')
            daily = df_copy.set_index('date').resample('D')['voted_up'].agg(['count', 'sum'])
            daily['positive_rate'] = daily['sum'] / daily['count']
            daily = daily.dropna()
            
            fig = px.bar(daily, y='count', title='Daily Review Count',
                        labels={'count': 'Reviews', 'index': 'Date'},
                        color='count', color_continuous_scale='blues')
            fig.update_layout(xaxis_title="Date", yaxis_title="Review Count")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Positive Rate Trend")
        if 'timestamp_created' in df.columns:
            df_copy = df.copy()
            df_copy['date'] = pd.to_datetime(df_copy['timestamp_created'], unit='s')
            daily = df_copy.set_index('date').resample('D')['voted_up'].agg(['count', 'sum'])
            daily['positive_rate'] = daily['sum'] / daily['count']
            daily = daily.dropna()
            
            fig = px.line(daily, y='positive_rate', title='Daily Positive Rate',
                        labels={'positive_rate': 'Positive Rate', 'index': 'Date'})
            fig.update_traces(line_color='#27ae60', line_width=2)
            fig.update_yaxes(tickformat='.0%', range=[0, 1])
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # ========== Row 3: Playtime & Review Length ==========
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⏱️ Playtime Distribution")
        if 'author.playtime_forever' in df.columns:
            df_copy = df.copy()
            df_copy['playtime_hours'] = pd.to_numeric(df_copy['author.playtime_forever'], errors='coerce') / 60
            df_copy = df_copy.dropna(subset=['playtime_hours'])
            
            # Bins
            bins = [0, 1, 5, 10, 20, 50, 100, 200, 500]
            labels = ['<1h', '1-5h', '5-10h', '10-20h', '20-50h', '50-100h', '100-200h', '200-500h']
            df_copy['playtime_bin'] = pd.cut(df_copy['playtime_hours'], bins=bins, labels=labels, right=False)
            
            playtime_counts = df_copy['playtime_bin'].value_counts().sort_index()
            fig = px.bar(x=playtime_counts.index, y=playtime_counts.values,
                        labels={'x': 'Playtime', 'y': 'Count'},
                        color=playtime_counts.values, color_continuous_scale='greens')
            fig.update_layout(xaxis_title="Playtime", yaxis_title="Number of Reviews")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📝 Review Length Distribution")
        if 'review' in df.columns:
            df_copy = df.copy()
            df_copy['review_length'] = df_copy['review'].astype(str).str.len()
            
            bins = [0, 50, 100, 200, 500, 1000, 5000]
            labels = ['<50', '50-100', '100-200', '200-500', '500-1000', '>1000']
            df_copy['length_bin'] = pd.cut(df_copy['review_length'], bins=bins, labels=labels, right=False)
            
            length_counts = df_copy['length_bin'].value_counts().sort_index()
            fig = px.bar(x=length_counts.index, y=length_counts.values,
                        labels={'x': 'Characters', 'y': 'Count'},
                        color=length_counts.values, color_continuous_scale='oranges')
            fig.update_layout(xaxis_title="Review Length", yaxis_title="Number of Reviews")
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # ========== Row 4: Early Access & Steam Deck ==========
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎮 Early Access Analysis")
        if 'written_during_early_access' in df.columns:
            ea_counts = df['written_during_early_access'].value_counts()
            fig = go.Figure(data=[go.Bar(
                x=['Not Early Access', 'Early Access'],
                y=[ea_counts.get(False, 0), ea_counts.get(True, 0)],
                marker_color=['#3498db', '#e67e22']
            )])
            fig.update_layout(xaxis_title="Type", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
            
            # Positive rate by early access
            ea_positive = df.groupby('written_during_early_access')['voted_up'].mean() * 100
            if True in ea_positive.index and False in ea_positive.index:
                st.write(f"**Positive Rate:** Not Early Access: {ea_positive.get(False, 0):.1f}% | Early Access: {ea_positive.get(True, 0):.1f}%")
    
    with col2:
        st.subheader("💻 Steam Deck Compatibility")
        if 'primarily_steam_deck' in df.columns:
            deck_counts = df['primarily_steam_deck'].value_counts()
            fig = go.Figure(data=[go.Pie(
                labels=['Desktop', 'Steam Deck'],
                values=[deck_counts.get(False, 0), deck_counts.get(True, 0)],
                marker=dict(colors=['#1abc9c', '#9b59b6']),
                hole=0.4
            )])
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # ========== Row 5: Generated Plots ==========
    st.subheader("📊 Analysis Charts")
    
    plots_dir = os.path.join(PROJECT_ROOT, 'plots')
    if os.path.exists(plots_dir) and csv_files:
        prefix = os.path.basename(csv_file).replace('.csv', '') if csv_file else ''
        plots = [f for f in os.listdir(plots_dir) if f.endswith('.png') and (prefix == '' or prefix in f)]
        
        # Show most relevant plots
        key_plots = [p for p in plots if any(x in p for x in ['sentiment', 'positive', 'negative', 'wordcloud', 'keywords'])]
        other_plots = [p for p in plots if p not in key_plots]
        
        if key_plots:
            st.write("**Key Charts:**")
            cols = st.columns(3)
            for i, plot in enumerate(key_plots[:6]):
                with cols[i % 3]:
                    st.image(f"{plots_dir}/{plot}", use_container_width=True)
        
        if other_plots:
            with st.expander("View More Charts"):
                cols = st.columns(3)
                for i, plot in enumerate(other_plots):
                    with cols[i % 3]:
                        st.image(f"{plots_dir}/{plot}", use_container_width=True)
    else:
        st.info("Run analysis to generate charts")
    
    st.divider()
    
    # ========== Recent Reviews ==========
    st.subheader("💬 Recent Reviews")
    display_cols = ['review', 'language', 'voted_up', 'timestamp_created']
    available_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[available_cols].head(10), use_container_width=True, height=400)


elif page == "🔍 Scrape":
    st.title("🔍 Scrape Reviews")
    
    col1, col2 = st.columns(2)
    
    with col1:
        app_id = st.text_input("Steam App ID", placeholder="e.g., 2277560")
        limit = st.number_input("Review Limit", min_value=0, value=1000, help="0 = unlimited")
    
    with col2:
        st.info("""
        **How to find App ID:**
        1. Go to Steam store page
        2. Look at the URL: store.steampowered.com/app/**2277560**
        3. The number at the end is the App ID
        """)
    
    if st.button("🚀 Start Scraping", type="primary"):
        if not app_id:
            st.error("Please enter an App ID")
        else:
            with st.spinner("Scraping reviews..."):
                try:
                    result = run_scrape(app_id, limit)
                    st.success(f"Scraping completed! File: {result}")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Recent files
    st.divider()
    st.subheader("Recent CSV Files")
    csv_files = get_csv_files()
    data_dir = os.path.join(PROJECT_ROOT, 'data')
    for f in csv_files[:5]:
        fpath = os.path.join(data_dir, f)
        if os.path.exists(fpath):
            size = os.path.getsize(fpath) / 1024
            st.write(f"📄 {f} ({size:.1f} KB)")


elif page == "📈 Analysis":
    st.title("📈 Analysis")
    
    csv_files = get_csv_files()
    if not csv_files:
        st.warning("No CSV files found. Scrape some reviews first!")
        st.stop()
    
    selected_file = st.selectbox("Select CSV File", csv_files)
    save_to_db = st.checkbox("Save to Database", value=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Run Analysis", type="primary"):
            with st.spinner("Analyzing reviews..."):
                try:
                    run_analyze(selected_file, save_to_db)
                    st.success("Analysis completed!")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        if st.button("📄 Generate Dashboard"):
            from src.steam_review.full_analysis import generate_full_analysis
            with st.spinner("Generating HTML dashboard..."):
                generate_full_analysis(selected_file, 'plots')
                st.success("Dashboard generated!")
    
    # Show existing plots
    st.divider()
    st.subheader("Generated Charts")
    
    plots_dir = os.path.join(PROJECT_ROOT, 'plots')
    if os.path.exists(plots_dir):
        # Find plots for selected file
        prefix = selected_file.replace('.csv', '')
        plots = [f for f in os.listdir(plots_dir) if prefix in f and f.endswith('.png')]
        
        if plots:
            cols = st.columns(3)
            for i, plot in enumerate(plots[:9]):
                with cols[i % 3]:
                    st.image(f"{PROJECT_ROOT}/plots/{plot}", caption=plot.replace(prefix + '_', '').replace('.png', ''))
        else:
            st.info("No plots generated yet. Run analysis first.")


elif page == "🔬 Advanced Analytics":
    st.title("🔬 Advanced Analytics")
    
    df = load_data(app_id_filter, 5000)
    
    if df.empty:
        st.warning("No data available. Go to 🔍 Scrape to fetch reviews.")
        st.stop()
    
    render_advanced_analytics(df, app_id_filter)


elif page == "💾 Database":
    st.title("💾 Database")
    
    # Stats
    stats = load_stats(app_id_filter)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", stats['total'])
    with col2:
        st.metric("Positive", stats['positive'])
    with col3:
        st.metric("Negative", stats['negative'])
    with col4:
        rate = stats['positive']/stats['total']*100 if stats['total'] > 0 else 0
        st.metric("Rate", f"{rate:.1f}%")
    
    st.divider()
    
    # Export
    st.subheader("Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox("Format", ["CSV", "Excel", "JSON"])
    
    with col2:
        filename = st.text_input("Filename", "reviews_export")
    
    if st.button("📥 Export"):
        db = get_database()
        import datetime
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            if export_format == "CSV":
                db.export_to_csv(f"{filename}_{ts}.csv", app_id_filter)
            elif export_format == "Excel":
                db.export_to_excel(f"{filename}_{ts}.xlsx", app_id_filter)
            else:
                db.export_to_json(f"{filename}_{ts}.json", app_id_filter)
            st.success(f"Exported to {filename}_{ts}")
        except Exception as e:
            st.error(f"Error: {e}")
    
    # Data preview
    st.divider()
    st.subheader("Data Preview")
    df = load_data(app_id_filter, 100)
    st.dataframe(df, use_container_width=True)


elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    
    st.subheader("About")
    st.info("""
    **Steam Review Analyzer**
    
    A comprehensive tool for scraping and analyzing Steam game reviews.
    
    **Features:**
    - Web scraping
    - Sentiment analysis
    - Keyword extraction
    - Topic modeling
    - Interactive dashboards
    """)
    
    st.subheader("Commands")
    st.code("""
# Scrape reviews
python cli.py scrape --app_id 2277560 --limit 1000

# Analyze
python cli.py analyze reviews.csv

# Full pipeline
python cli.py run --app_id 2277560

# Web dashboard
python cli.py dashboard

# API server
python cli.py serve
    """)
    
    st.subheader("Files")
    st.write(f"CSV files: {len(get_csv_files())}")
    db_path = os.path.join(PROJECT_ROOT, 'data', 'reviews.db')
    if os.path.exists(db_path):
        st.write(f"Database: reviews.db ({os.path.getsize(db_path)/1024:.1f} KB)")
    else:
        st.write("Database: Not found")


if __name__ == "__main__":
    pass  # Streamlit handles this
