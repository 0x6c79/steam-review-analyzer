import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_database
import config

config.setup_logging()

st.set_page_config(
    page_title="Steam Review Analytics",
    page_icon="🎮",
    layout="wide"
)


@st.cache_data
def load_data(app_id=None, limit=1000):
    db = get_database()
    return db.get_reviews(app_id, limit)


@st.cache_data
def load_stats(app_id=None):
    db = get_database()
    return db.get_stats(app_id)


st.title("🎮 Steam Review Analytics Dashboard")

with st.sidebar:
    st.header("Settings")
    
    db = get_database()
    df_db = db.get_reviews()
    
    if not df_db.empty and 'app_id' in df_db.columns:
        app_ids = df_db['app_id'].unique().tolist()
        selected_app = st.selectbox("Select App ID", ["All"] + app_ids)
        app_id_filter = None if selected_app == "All" else selected_app
    else:
        app_id_filter = None
        selected_app = "All"
    
    st.divider()
    
    st.subheader("Data Actions")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()


stats = load_stats(app_id_filter)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Reviews", stats['total'])

with col2:
    st.metric("Positive Reviews", stats['positive'])

with col3:
    st.metric("Negative Reviews", stats['negative'])

with col4:
    rate = (stats['positive'] / stats['total'] * 100) if stats['total'] > 0 else 0
    st.metric("Positive Rate", f"{rate:.1f}%")


st.divider()

df = load_data(app_id_filter, limit=2000)

if df.empty:
    st.warning("No data available. Please scrape some reviews first.")
    st.stop()


tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Trends", "🔍 Reviews", "⚙️ Settings"])


with tab1:
    st.subheader("Sentiment Distribution")
    
    if 'voted_up' in df.columns:
        vote_counts = df['voted_up'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Positive', 'Negative'],
                values=[vote_counts.get(True, 0), vote_counts.get(False, 0)],
                marker=dict(colors=['#4CAF50', '#F44336'])
            )])
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            if 'timestamp_created' in df.columns:
                df['date'] = pd.to_datetime(df['timestamp_created'], unit='s')
                daily = df.set_index('date').resample('D')['voted_up'].mean()
                
                fig_line = px.line(
                    x=daily.index, 
                    y=daily.values,
                    labels={'x': 'Date', 'y': 'Positive Rate'},
                    title="Daily Positive Rate Trend"
                )
                fig_line.update_traces(line_color='#2196F3')
                st.plotly_chart(fig_line, use_container_width=True)


with tab2:
    st.subheader("Review Trends Over Time")
    
    if 'timestamp_created' in df.columns:
        df['date'] = pd.to_datetime(df['timestamp_created'], unit='s')
        
        time_period = st.selectbox("Time Period", ["Daily", "Weekly", "Monthly"])
        
        if time_period == "Daily":
            period = 'D'
        elif time_period == "Weekly":
            period = 'W'
        else:
            period = 'M'
        
        grouped = df.set_index('date').resample(period).agg({
            'voted_up': ['count', 'sum', 'mean']
        })
        grouped.columns = ['total', 'positive', 'positive_rate']
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=grouped.index, 
            y=grouped['total'],
            name="Total Reviews",
            marker_color='#2196F3'
        ))
        fig.add_trace(go.Scatter(
            x=grouped.index, 
            y=grouped['positive_rate'] * 100,
            name="Positive Rate %",
            yaxis='y2',
            line=dict(color='#FF9800', width=2)
        ))
        
        fig.update_layout(
            yaxis=dict(title="Total Reviews"),
            yaxis2=dict(title="Positive Rate %", overlaying='y', side='right'),
            legend=dict(x=0, y=1.1, orientation='h'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)


with tab3:
    st.subheader("Review Browser")
    
    if 'language' in df.columns:
        languages = df['language'].unique().tolist()
        selected_lang = st.multiselect("Filter by Language", languages, default=languages[:3])
        
        if selected_lang:
            df_filtered = df[df['language'].isin(selected_lang)]
        else:
            df_filtered = df
    else:
        df_filtered = df
    
    show_voted_up = st.radio("Filter by Vote", ["All", "Positive", "Negative"])
    
    if show_voted_up == "Positive":
        df_filtered = df_filtered[df_filtered['voted_up'] == True]
    elif show_voted_up == "Negative":
        df_filtered = df_filtered[df_filtered['voted_up'] == False]
    
    st.dataframe(
        df_filtered[['review', 'language', 'voted_up', 'timestamp_created']].head(50),
        height=400,
        use_container_width=True
    )


with tab4:
    st.subheader("Application Settings")
    
    st.write("### API Endpoints")
    st.code("""
# Start API server
python api.py

# API will be available at:
# http://localhost:8000
# API docs: http://localhost:8000/docs
    """)
    
    st.write("### Scheduled Tasks")
    st.code("""
# Run scheduler
python scheduler.py --app_ids 2277560 1091500 --interval 24
    """)
    
    st.write("### Database Export")
    st.code("""
# Export to CSV
python export_cli.py export --format csv --output data.csv

# Export to Excel
python export_cli.py export --format excel --output data.xlsx

# Export to JSON
python export_cli.py export --format json --output data.json
    """)
    
    st.write("### Alerts Configuration")
    st.info("Edit alerts.py to customize alert rules and handlers")


st.divider()
st.caption("Steam Review Analytics - Built with Streamlit")
