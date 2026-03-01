"""
Advanced filter UI components for the Streamlit dashboard.
Provides reusable filter widgets with state management.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class FilterManager:
    """Manages filter state and UI for dashboard filtering."""
    
    FILTER_STATE_KEY = "dashboard_filters"
    
    @staticmethod
    def init_filters() -> None:
        """Initialize filter state in session."""
        if FilterManager.FILTER_STATE_KEY not in st.session_state:
            st.session_state[FilterManager.FILTER_STATE_KEY] = {
                'date_range_enabled': False,
                'start_date': None,
                'end_date': None,
                'playtime_range_enabled': False,
                'min_playtime': 0,
                'max_playtime': 100,
                'language_filter_enabled': False,
                'selected_languages': [],
                'sentiment_filter_enabled': False,
                'min_sentiment': 0.0,
                'max_sentiment': 1.0,
                'voted_up_only': False,
            }
    
    @staticmethod
    def get_filters() -> Dict[str, Any]:
        """Get current filter state."""
        FilterManager.init_filters()
        return st.session_state[FilterManager.FILTER_STATE_KEY]
    
    @staticmethod
    def reset_filters() -> None:
        """Reset all filters to default."""
        if FilterManager.FILTER_STATE_KEY in st.session_state:
            del st.session_state[FilterManager.FILTER_STATE_KEY]
        FilterManager.init_filters()


class DashboardFilters:
    """Advanced filter UI components for the dashboard."""
    
    @staticmethod
    def render_filters(
        metadata: Optional[Dict[str, Any]] = None,
        app_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Render advanced filter UI and return active filters.
        
        Args:
            metadata: Metadata dict with date_range, playtime_range, languages
            app_id: Current selected app ID
        
        Returns:
            Dictionary of active filters to use in queries
        """
        FilterManager.init_filters()
        filters = FilterManager.get_filters()
        
        st.subheader("🔍 Advanced Filters")
        
        # Create tabs for different filter types
        filter_tabs = st.tabs(["Date & Time", "Playtime", "Language", "Sentiment", "Custom"])
        
        active_filters = {}
        
        # ========== DATE RANGE FILTERS ==========
        with filter_tabs[0]:
            col1, col2 = st.columns(2)
            
            with col1:
                enable_date_filter = st.checkbox(
                    "Filter by Date Range",
                    value=filters['date_range_enabled'],
                    key="date_filter_enable"
                )
                filters['date_range_enabled'] = enable_date_filter
            
            if enable_date_filter:
                with col2:
                    st.info("Select review creation date range")
                
                # Get date range from metadata or use defaults
                if metadata and 'date_range' in metadata:
                    min_date = metadata['date_range']['min']
                    max_date = metadata['date_range']['max']
                    if min_date is None:
                        min_date = pd.Timestamp.now() - pd.Timedelta(days=365)
                    if max_date is None:
                        max_date = pd.Timestamp.now()
                else:
                    min_date = pd.Timestamp.now() - pd.Timedelta(days=365)
                    max_date = pd.Timestamp.now()
                
                col_start, col_end = st.columns(2)
                
                with col_start:
                    start_date = st.date_input(
                        "Start Date",
                        value=filters['start_date'] or min_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="date_start"
                    )
                    filters['start_date'] = start_date
                    active_filters['start_date'] = start_date
                
                with col_end:
                    end_date = st.date_input(
                        "End Date",
                        value=filters['end_date'] or max_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="date_end"
                    )
                    filters['end_date'] = end_date
                    active_filters['end_date'] = end_date
        
        # ========== PLAYTIME FILTERS ==========
        with filter_tabs[1]:
            col1, col2 = st.columns(2)
            
            with col1:
                enable_playtime_filter = st.checkbox(
                    "Filter by Playtime",
                    value=filters['playtime_range_enabled'],
                    key="playtime_filter_enable"
                )
                filters['playtime_range_enabled'] = enable_playtime_filter
            
            if enable_playtime_filter:
                with col2:
                    st.info("Hours played (estimated)")
                
                # Get playtime range from metadata
                if metadata and 'playtime_range' in metadata:
                    max_pt = metadata['playtime_range']['max']
                else:
                    max_pt = 1000
                
                min_pt, max_pt_filter = st.slider(
                    "Playtime Range (hours)",
                    min_value=0,
                    max_value=int(max_pt) + 100,
                    value=(
                        int(filters['min_playtime']),
                        int(filters['max_playtime'])
                    ),
                    step=10,
                    key="playtime_slider"
                )
                
                filters['min_playtime'] = min_pt
                filters['max_playtime'] = max_pt_filter
                active_filters['min_playtime'] = min_pt
                active_filters['max_playtime'] = max_pt_filter
                
                st.caption(f"Selected: {min_pt} - {max_pt_filter} hours")
        
        # ========== LANGUAGE FILTERS ==========
        with filter_tabs[2]:
            col1, col2 = st.columns(2)
            
            with col1:
                enable_lang_filter = st.checkbox(
                    "Filter by Language",
                    value=filters['language_filter_enabled'],
                    key="lang_filter_enable"
                )
                filters['language_filter_enabled'] = enable_lang_filter
            
            if enable_lang_filter:
                # Get available languages
                available_langs = []
                if metadata and 'languages' in metadata:
                    available_langs = sorted([l for l in metadata['languages'] if l])
                
                if available_langs:
                    selected_langs = st.multiselect(
                        "Select Languages",
                        options=available_langs,
                        default=filters['selected_languages'],
                        key="language_multiselect"
                    )
                    filters['selected_languages'] = selected_langs
                    if selected_langs:
                        active_filters['languages'] = selected_langs
                else:
                    st.warning("No language data available")
        
        # ========== SENTIMENT FILTERS ==========
        with filter_tabs[3]:
            col1, col2 = st.columns(2)
            
            with col1:
                enable_sentiment = st.checkbox(
                    "Filter by Sentiment",
                    value=filters['sentiment_filter_enabled'],
                    key="sentiment_filter_enable"
                )
                filters['sentiment_filter_enabled'] = enable_sentiment
            
            if enable_sentiment:
                with col2:
                    st.info("Only show reviews with specific sentiment scores")
                
                min_sent, max_sent = st.slider(
                    "Sentiment Score Range (0=negative, 1=positive)",
                    min_value=0.0,
                    max_value=1.0,
                    value=(
                        float(filters['min_sentiment']),
                        float(filters['max_sentiment'])
                    ),
                    step=0.05,
                    key="sentiment_slider"
                )
                
                filters['min_sentiment'] = min_sent
                filters['max_sentiment'] = max_sent
                active_filters['sentiment_min'] = min_sent
                active_filters['sentiment_max'] = max_sent
        
        # ========== CUSTOM FILTERS ==========
        with filter_tabs[4]:
            voted_up_only = st.checkbox(
                "Show Only Positive Reviews",
                value=filters['voted_up_only'],
                key="voted_up_filter"
            )
            filters['voted_up_only'] = voted_up_only
            if voted_up_only:
                active_filters['voted_up_only'] = True
            
            st.divider()
            
            # Filter summary
            st.subheader("📋 Active Filters")
            if active_filters:
                for key, value in active_filters.items():
                    st.caption(f"✓ {key}: {value}")
            else:
                st.caption("No filters applied")
            
            # Clear filters button
            if st.button("🔄 Reset All Filters", use_container_width=True):
                FilterManager.reset_filters()
                st.rerun()
        
        # Update session state
        st.session_state[FilterManager.FILTER_STATE_KEY] = filters
        
        return active_filters


class ExportUI:
    """Export functionality UI components."""
    
    @staticmethod
    def render_export_options(df: pd.DataFrame, app_id: Optional[str] = None) -> None:
        """
        Render export options UI.
        
        Args:
            df: DataFrame to export
            app_id: Optional app ID for file naming
        """
        st.subheader("📥 Export Data")
        
        col1, col2, col3 = st.columns(3)
        
        # Generate filename
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        game_name = app_id or "reviews"
        base_filename = f"steam_reviews_{game_name}_{timestamp}"
        
        with col1:
            if st.button("📊 Download CSV", use_container_width=True):
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="💾 CSV File",
                    data=csv_data,
                    file_name=f"{base_filename}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col2:
            if st.button("📈 Download Excel", use_container_width=True):
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Reviews')
                    # Format header row
                    worksheet = writer.sheets['Reviews']
                    for cell in worksheet[1]:
                        cell.font = cell.font.copy(bold=True)
                
                buffer.seek(0)
                st.download_button(
                    label="💾 Excel File",
                    data=buffer.getvalue(),
                    file_name=f"{base_filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        with col3:
            if st.button("📋 Download JSON", use_container_width=True):
                json_data = df.to_json(orient='records', force_ascii=False, indent=2)
                st.download_button(
                    label="💾 JSON File",
                    data=json_data,
                    file_name=f"{base_filename}.json",
                    mime="application/json",
                    use_container_width=True
                )


class DarkModeUI:
    """Dark mode theme support."""
    
    @staticmethod
    def apply_theme() -> None:
        """Apply dark/light theme based on user preference."""
        if 'theme_mode' not in st.session_state:
            st.session_state.theme_mode = 'light'
    
    @staticmethod
    def render_theme_toggle() -> None:
        """Render theme toggle in sidebar."""
        with st.sidebar:
            st.divider()
            st.subheader("🎨 Appearance")
            
            theme_options = ["Light", "Dark", "Auto"]
            current_theme = st.selectbox(
                "Theme",
                options=theme_options,
                index=0 if st.session_state.get('theme_mode') == 'light' else 1
            )
            
            st.session_state.theme_mode = current_theme.lower()
            
            # Note: Full dark mode requires Streamlit config or custom CSS
            st.info("💡 Tip: Use Streamlit's built-in dark mode in settings")
