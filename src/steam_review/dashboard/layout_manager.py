"""
Layout configuration for customizable dashboard layouts.
Provides preset and custom layout options for different use cases.
"""

import streamlit as st
import logging
from enum import Enum
from typing import Literal, Dict, Any, List

logger = logging.getLogger(__name__)


class LayoutMode(Enum):
    """Available dashboard layout modes."""
    COMPACT = "compact"  # Single column, minimal spacing
    BALANCED = "balanced"  # Two columns, moderate spacing
    WIDE = "wide"  # Three columns, ample spacing
    CUSTOM = "custom"  # User-defined layout


class DashboardLayout:
    """Manages dashboard layout preferences and rendering."""
    
    LAYOUT_STATE_KEY = "dashboard_layout"
    
    # Preset configurations
    PRESETS = {
        LayoutMode.COMPACT: {
            'columns': 1,
            'column_width': [1.0],
            'spacing': 'small',
            'chart_height': 400,
            'show_sidebar': True,
            'show_metrics': True,
            'description': 'Single column layout for detailed focus'
        },
        LayoutMode.BALANCED: {
            'columns': 2,
            'column_width': [0.5, 0.5],
            'spacing': 'medium',
            'chart_height': 450,
            'show_sidebar': True,
            'show_metrics': True,
            'description': 'Two column balanced layout'
        },
        LayoutMode.WIDE: {
            'columns': 3,
            'column_width': [0.33, 0.33, 0.34],
            'spacing': 'large',
            'chart_height': 500,
            'show_sidebar': True,
            'show_metrics': True,
            'description': 'Three column wide layout for overview'
        },
    }
    
    @staticmethod
    def init_layout() -> None:
        """Initialize layout state in session."""
        if DashboardLayout.LAYOUT_STATE_KEY not in st.session_state:
            st.session_state[DashboardLayout.LAYOUT_STATE_KEY] = {
                'mode': LayoutMode.BALANCED,
                'columns': 2,
                'spacing': 'medium',
                'chart_height': 450,
                'show_sidebar': True,
                'show_metrics': True,
                'custom_enabled': False,
            }
    
    @staticmethod
    def get_layout() -> Dict[str, Any]:
        """Get current layout configuration."""
        DashboardLayout.init_layout()
        return st.session_state[DashboardLayout.LAYOUT_STATE_KEY]
    
    @staticmethod
    def set_layout(mode: LayoutMode) -> None:
        """Set layout to a preset mode."""
        DashboardLayout.init_layout()
        if mode in DashboardLayout.PRESETS:
            config = DashboardLayout.PRESETS[mode]
            st.session_state[DashboardLayout.LAYOUT_STATE_KEY] = {
                'mode': mode,
                'columns': config['columns'],
                'spacing': config['spacing'],
                'chart_height': config['chart_height'],
                'show_sidebar': config['show_sidebar'],
                'show_metrics': config['show_metrics'],
                'custom_enabled': False,
            }
            logger.info(f"Layout set to {mode.value}")
    
    @staticmethod
    def render_layout_selector() -> None:
        """Render layout selection UI in sidebar."""
        with st.sidebar:
            st.divider()
            st.subheader("📐 Layout & Display")
            
            col1, col2 = st.columns(2)
            
            with col1:
                layout_names = [mode.value.capitalize() for mode in LayoutMode if mode != LayoutMode.CUSTOM]
                current_mode = DashboardLayout.get_layout()['mode']
                selected_idx = list(LayoutMode)[:-1].index(current_mode) if current_mode in list(LayoutMode)[:-1] else 1
                
                selected = st.selectbox(
                    "Layout Mode",
                    options=layout_names,
                    index=selected_idx,
                    key="layout_selector"
                )
                
                # Map selection back to mode
                mode_map = {mode.value.capitalize(): mode for mode in list(LayoutMode)[:-1]}
                if selected in mode_map:
                    DashboardLayout.set_layout(mode_map[selected])
            
            with col2:
                # Show info about current layout
                current_layout = DashboardLayout.get_layout()
                if current_layout['mode'] in DashboardLayout.PRESETS:
                    preset = DashboardLayout.PRESETS[current_layout['mode']]
                    st.caption(f"Columns: {preset['columns']}")
            
            # Display options
            col1, col2 = st.columns(2)
            
            with col1:
                show_sidebar = st.checkbox(
                    "Show Sidebar",
                    value=DashboardLayout.get_layout()['show_sidebar'],
                    key="show_sidebar_checkbox"
                )
                DashboardLayout.get_layout()['show_sidebar'] = show_sidebar
            
            with col2:
                show_metrics = st.checkbox(
                    "Show Metrics",
                    value=DashboardLayout.get_layout()['show_metrics'],
                    key="show_metrics_checkbox"
                )
                DashboardLayout.get_layout()['show_metrics'] = show_metrics
            
            # Chart height customization
            chart_height = st.slider(
                "Chart Height (px)",
                min_value=300,
                max_value=800,
                value=DashboardLayout.get_layout()['chart_height'],
                step=50,
                key="chart_height_slider"
            )
            DashboardLayout.get_layout()['chart_height'] = chart_height


class LayoutRenderer:
    """Utilities for rendering content with configured layout."""
    
    @staticmethod
    def get_columns_for_layout(num_charts: int) -> List[Any]:
        """
        Get Streamlit columns based on layout configuration.
        
        Args:
            num_charts: Number of charts to display
        
        Returns:
            List of Streamlit column objects
        """
        layout = DashboardLayout.get_layout()
        cols_count = min(layout['columns'], num_charts)
        
        # Adjust spacing based on configuration
        if layout['spacing'] == 'small':
            gap = 'small'
        elif layout['spacing'] == 'large':
            gap = 'large'
        else:
            gap = 'medium'
        
        return st.columns(cols_count, gap=gap)
    
    @staticmethod
    def create_responsive_chart_container(use_container_width: bool = True) -> Dict[str, Any]:
        """
        Create responsive chart configuration based on layout.
        
        Returns:
            Dictionary with chart configuration
        """
        layout = DashboardLayout.get_layout()
        return {
            'height': layout['chart_height'],
            'use_container_width': use_container_width,
            'margin': dict(l=50, r=50, t=50, b=50)
        }
    
    @staticmethod
    def render_metric_grid(metrics: Dict[str, str]) -> None:
        """
        Render metrics in a grid based on layout.
        
        Args:
            metrics: Dictionary of metric_name -> metric_value
        """
        layout = DashboardLayout.get_layout()
        
        if not layout['show_metrics']:
            return
        
        metrics_list = list(metrics.items())
        cols_count = min(layout['columns'], len(metrics_list))
        cols = st.columns(cols_count)
        
        for idx, (name, value) in enumerate(metrics_list):
            col_idx = idx % cols_count
            with cols[col_idx]:
                st.metric(name, value)


class ViewportManager:
    """Manages responsive viewport behavior."""
    
    @staticmethod
    def get_viewport_width() -> Literal['mobile', 'tablet', 'desktop']:
        """
        Determine viewport width category.
        Uses Streamlit session state to track approximated width.
        
        Returns:
            'mobile', 'tablet', or 'desktop'
        """
        # Streamlit's default width is ~1200px
        # We can estimate based on layout
        layout = DashboardLayout.get_layout()
        
        if layout['columns'] == 1:
            return 'mobile'
        elif layout['columns'] == 2:
            return 'tablet'
        else:
            return 'desktop'
    
    @staticmethod
    def is_mobile() -> bool:
        """Check if viewport is mobile-sized."""
        return ViewportManager.get_viewport_width() == 'mobile'
    
    @staticmethod
    def is_tablet() -> bool:
        """Check if viewport is tablet-sized."""
        return ViewportManager.get_viewport_width() == 'tablet'
    
    @staticmethod
    def is_desktop() -> bool:
        """Check if viewport is desktop-sized."""
        return ViewportManager.get_viewport_width() == 'desktop'


class ThemeConfig:
    """Theme and styling configuration."""
    
    # Color schemes
    COLOR_SCHEMES = {
        'light': {
            'primary': '#1f77b4',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'info': '#3498db',
            'bg_primary': '#ffffff',
            'bg_secondary': '#f8f9fa',
            'text_primary': '#2c3e50',
            'text_secondary': '#7f8c8d',
        },
        'dark': {
            'primary': '#3498db',
            'success': '#2ecc71',
            'warning': '#f1c40f',
            'danger': '#e74c3c',
            'info': '#9b59b6',
            'bg_primary': '#2c3e50',
            'bg_secondary': '#34495e',
            'text_primary': '#ecf0f1',
            'text_secondary': '#bdc3c7',
        },
    }
    
    @staticmethod
    def get_color_scheme(theme: str = 'light') -> Dict[str, str]:
        """Get color scheme for theme."""
        return ThemeConfig.COLOR_SCHEMES.get(theme, ThemeConfig.COLOR_SCHEMES['light'])
    
    @staticmethod
    def render_theme_css(theme: str = 'light') -> None:
        """Render theme CSS."""
        colors = ThemeConfig.get_color_scheme(theme)
        
        css = f"""
        <style>
            :root {{
                --primary-color: {colors['primary']};
                --success-color: {colors['success']};
                --warning-color: {colors['warning']};
                --danger-color: {colors['danger']};
                --bg-primary: {colors['bg_primary']};
            }}
            
            .main {{
                background-color: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
            
            .stat-card {{
                background-color: {colors['bg_secondary']};
                border-left: 4px solid {colors['primary']};
            }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
