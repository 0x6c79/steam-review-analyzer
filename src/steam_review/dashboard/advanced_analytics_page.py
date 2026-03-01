#!/usr/bin/env python3
"""
Advanced Analytics Dashboard Page for Streamlit
Integrates all advanced analysis features
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
import sys
import os

# Add project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.steam_review.analysis.advanced_analyzer import AdvancedReviewAnalyzer
from src.steam_review.analysis.keyword_extractor import KeywordAndTopicExtractor


@st.cache_data
def run_advanced_analysis(df):
    """Run all advanced analyses"""
    if df.empty:
        return None
    
    analyzer = AdvancedReviewAnalyzer(df)
    
    # Run analyses
    sentiment_intensity = analyzer.analyze_sentiment_intensity()
    analyzer.calculate_quality_score()
    issues = analyzer.detect_issues()
    segments = analyzer.segment_players()
    temporal = analyzer.analyze_temporal_trends()
    
    return {
        'analyzer': analyzer,
        'sentiment_intensity': sentiment_intensity,
        'issues': issues,
        'segments': segments,
        'temporal': temporal
    }


@st.cache_data
def run_keyword_analysis(df):
    """Run keyword and topic analysis"""
    if df.empty:
        return None
    
    try:
        extractor = KeywordAndTopicExtractor(df)
        return {
            'keywords': extractor.extract_keywords(top_n=30),
            'bigrams': extractor.extract_bigrams(top_n=20),
            'topics': extractor.extract_topics(num_topics=6),
            'sentiment_by_topic': extractor.sentiment_by_topic(),
            'word_cloud_data': extractor.generate_word_cloud_data(top_n=50)
        }
    except Exception as e:
        st.error(f"Keyword analysis error: {e}")
        return None


def render_advanced_analytics(df, app_id_filter=None):
    """Main function to render advanced analytics page"""
    
    if df.empty:
        st.warning("No data available. Please scrape some reviews first!")
        return
    
    # Run analyses
    analysis_results = run_advanced_analysis(df)
    keyword_results = run_keyword_analysis(df)
    
    if not analysis_results:
        st.error("Failed to run analysis")
        return
    
    analyzer = analysis_results['analyzer']
    
    # ==================== TABS ====================
    tabs = st.tabs([
        "📊 情感分析",
        "🔍 关键词&主题",
        "⭐ 质量评分",
        "🐛 问题识别",
        "👥 玩家分段",
        "📈 时间趋势",
        "💡 顶级评论"
    ])
    
    # ==================== TAB 1: 情感分析 ====================
    with tabs[0]:
        st.subheader("情感强度分析")
        st.markdown("超越简单的正负面，深入分析情感的强度")
        
        sentiment_intensity = analysis_results['sentiment_intensity']
        
        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        dist = sentiment_intensity['distribution']
        colors_map = {
            'Very Positive': '#27ae60',
            'Positive': '#52be80',
            'Negative': '#f8b88b',
            'Very Negative': '#e74c3c'
        }
        
        with col1:
            st.metric("非常满意", dist.get('Very Positive', 0))
        with col2:
            st.metric("满意", dist.get('Positive', 0))
        with col3:
            st.metric("不满意", dist.get('Negative', 0))
        with col4:
            st.metric("非常不满意", dist.get('Very Negative', 0))
        
        # Pie chart
        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure(data=[go.Pie(
                labels=list(dist.keys()),
                values=list(dist.values()),
                marker=dict(colors=[colors_map.get(k, '#95a5a6') for k in dist.keys()]),
                hole=0.3
            )])
            fig.update_layout(title="情感强度分布", height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Sentiment intensity over time
            df_copy = df.copy()
            df_copy['sentiment_intensity'] = analyzer.df['sentiment_intensity']
            if 'timestamp_created' in df_copy.columns:
                df_copy['date'] = pd.to_datetime(df_copy['timestamp_created'], unit='s')
                daily_sentiment = df_copy.groupby(df_copy['date'].dt.date)['voted_up'].agg(['sum', 'count'])
                daily_sentiment['rate'] = (daily_sentiment['sum'] / daily_sentiment['count'] * 100).round(1)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_sentiment.index,
                    y=daily_sentiment['rate'],
                    mode='lines+markers',
                    name='满意度',
                    line=dict(color='#3498db', width=2)
                ))
                fig.update_layout(title="满意度趋势", xaxis_title="日期", yaxis_title="满意度%", height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    # ==================== TAB 2: 关键词&主题 ====================
    with tabs[1]:
        st.subheader("关键词和主题提取")
        
        if keyword_results:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🔤 高频关键词")
                keywords = keyword_results['keywords']['keywords']
                keyword_df = pd.DataFrame(list(keywords.items()), columns=['关键词', '频次'])
                keyword_df = keyword_df.head(20)
                
                fig = px.bar(keyword_df, x='频次', y='关键词', orientation='h',
                           color='频次', color_continuous_scale='Blues')
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### 📚 主要主题")
                topics = keyword_results['topics']['topics']
                topics_df = pd.DataFrame(list(topics.items()), columns=['主题', '权重'])
                
                fig = px.bar(topics_df, x='权重', y='主题', orientation='h',
                           color='权重', color_continuous_scale='Greens')
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            # Topic sentiment analysis
            st.markdown("#### 📊 各主题的满意度")
            topic_sentiment = keyword_results['sentiment_by_topic']
            if topic_sentiment:
                topic_df = pd.DataFrame(topic_sentiment).T.reset_index()
                topic_df.columns = ['主题', 'review_count', 'positive_rate', 'percentage']
                
                fig = px.bar(topic_df, x='主题', y='positive_rate',
                           color='positive_rate', color_continuous_scale='RdYlGn',
                           hover_data=['review_count', 'percentage'])
                fig.update_layout(height=400, yaxis_title="满意度百分比(%)")
                st.plotly_chart(fig, use_container_width=True)
            
            # Common phrases
            st.markdown("#### 💬 常见短语")
            bigrams = keyword_results['bigrams']['bigrams']
            bigram_df = pd.DataFrame(list(bigrams.items()), columns=['短语', '频次']).head(15)
            
            fig = px.bar(bigram_df, x='频次', y='短语', orientation='h',
                       color='频次', color_continuous_scale='Purples')
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    # ==================== TAB 3: 质量评分 ====================
    with tabs[2]:
        st.subheader("评论质量评分")
        st.markdown("基于长度、详细程度、结构等多个维度评估评论质量")
        
        quality_scores = analyzer.df['quality_score']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("平均质量分", f"{quality_scores.mean():.1f}")
        with col2:
            st.metric("最高分", f"{quality_scores.max():.0f}")
        with col3:
            st.metric("最低分", f"{quality_scores.min():.0f}")
        with col4:
            st.metric("中位数", f"{quality_scores.median():.1f}")
        
        # Distribution chart
        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure(data=[go.Histogram(x=quality_scores, nbinsx=20, name='质量分')])
            fig.update_layout(title="质量分分布", xaxis_title="质量分", yaxis_title="评论数", height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Quality vs sentiment
            df_copy = df.copy()
            df_copy['quality_score'] = analyzer.df['quality_score']
            df_copy['sentiment'] = df_copy['voted_up'].map({True: 'Positive', False: 'Negative'})
            
            fig = px.scatter(df_copy, x='quality_score', y='sentiment', 
                           color='sentiment',
                           color_discrete_map={'Positive': '#27ae60', 'Negative': '#e74c3c'},
                           labels={'sentiment': '情感', 'quality_score': '质量分'},
                           title='质量分布与情感关联')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Top quality reviews
        st.markdown("#### ⭐ 最优质的评论")
        top_reviews = analyzer.get_top_reviews(n=3, by='quality')
        for idx, (_, review) in enumerate(top_reviews.iterrows(), 1):
            with st.expander(f"评论 #{idx} (质量分: {review['quality_score']:.0f})"):
                st.write(review['review'][:500] + "...")
    
    # ==================== TAB 4: 问题识别 ====================
    with tabs[3]:
        st.subheader("常见问题和吐槽")
        st.markdown("自动识别评论中提到的常见问题")
        
        issues = analysis_results['issues']
        issue_count = issues['issue_count']
        
        # Top issues
        issue_df = pd.DataFrame(list(issue_count.items()), columns=['问题类型', '提及次数'])
        issue_df = issue_df[issue_df['提及次数'] > 0].sort_values('提及次数', ascending=False)
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(issue_df, x='提及次数', y='问题类型', orientation='h',
                       color='提及次数', color_continuous_scale='Reds')
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Issue percentages
            issue_pct = issues['issue_percentage']
            pct_df = pd.DataFrame(list(issue_pct.items()), columns=['问题', '占比'])
            pct_df['占比'] = pct_df['占比'].str.rstrip('%').astype(float)
            pct_df = pct_df[pct_df['占比'] > 0].sort_values('占比', ascending=False)
            
            fig = px.pie(pct_df, values='占比', names='问题',
                        hole=0.3)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Issue details
        st.markdown("#### 🔍 问题详情")
        for issue_type, count in sorted(issue_count.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{issue_type}**")
                with col2:
                    st.write(f"{count} 条评论")
    
    # ==================== TAB 5: 玩家分段 ====================
    with tabs[4]:
        st.subheader("玩家分段分析")
        st.markdown("根据评论特征将玩家分为不同类型")
        
        segments = analysis_results['segments']
        
        col1, col2, col3 = st.columns(3)
        for i, (segment_name, count) in enumerate(segments['segments'].items()):
            with [col1, col2, col3][i % 3]:
                st.metric(
                    segment_name,
                    count,
                    segments['percentages'][segment_name]
                )
        
        # Segment distribution
        col1, col2 = st.columns(2)
        with col1:
            seg_df = pd.DataFrame(list(segments['segments'].items()), columns=['玩家类型', '数量'])
            fig = px.pie(seg_df, values='数量', names='玩家类型')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Segment characteristics
            st.markdown("#### 📋 玩家类型特征")
            characteristics = {
                'Enthusiasts': '🌟 热情粉丝 - 详细的正面评论',
                'Satisfied': '😊 满意玩家 - 正面评价',
                'Cautious': '🤔 谨慎玩家 - 既有优点也有疑虑',
                'Dissatisfied': '😞 不满意 - 有疑虑的玩家',
                'Critical': '😠 批评者 - 详细的负面评论'
            }
            for seg_type, desc in characteristics.items():
                st.write(f"{desc}")
    
    # ==================== TAB 6: 时间趋势 ====================
    with tabs[5]:
        st.subheader("评论趋势分析")
        st.markdown("分析评论数量和满意度随时间的变化")
        
        if 'timestamp_created' in df.columns:
            df_temp = df.copy()
            df_temp['date'] = pd.to_datetime(df_temp['timestamp_created'], unit='s')
            
            # Daily stats
            daily_stats = df_temp.groupby(df_temp['date'].dt.date).agg({
                'voted_up': ['count', 'sum', 'mean']
            }).round(3)
            daily_stats.columns = ['review_count', 'positive_count', 'positive_rate']
            daily_stats['positive_rate'] = (daily_stats['positive_rate'] * 100).round(1)
            
            # Multiple metrics
            col1, col2 = st.columns(2)
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_stats.index,
                    y=daily_stats['review_count'],
                    mode='lines+markers',
                    name='评论数',
                    line=dict(color='#3498db')
                ))
                fig.update_layout(title="每日评论数", height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_stats.index,
                    y=daily_stats['positive_rate'],
                    mode='lines+markers',
                    name='满意度%',
                    line=dict(color='#27ae60', width=2),
                    fill='tozeroy'
                ))
                fig.update_layout(title="每日满意度", yaxis_title="满意度(%)", height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    # ==================== TAB 7: 顶级评论 ====================
    with tabs[6]:
        st.subheader("最值得一读的评论")
        st.markdown("按质量评分排序，展示最详细、最有帮助的评论")
        
        tabs_quality = st.tabs(["按质量排序", "按有用性排序"])
        
        with tabs_quality[0]:
            top_quality = analyzer.get_top_reviews(n=5, by='quality')
            for idx, (_, review) in enumerate(top_quality.iterrows(), 1):
                with st.expander(f"评论 #{idx} (质量分: {review['quality_score']:.0f})"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        sentiment = "👍 推荐" if review['voted_up'] else "👎 不推荐"
                        st.write(f"**{sentiment}**")
                    with col2:
                        st.write(f"质量: {review['quality_score']:.0f}/100")
                    st.write(review['review'][:800])
        
        with tabs_quality[1]:
            top_helpful = analyzer.get_top_reviews(n=5, by='helpful')
            for idx, (_, review) in enumerate(top_helpful.iterrows(), 1):
                with st.expander(f"评论 #{idx} (有用度: {review['voted_up']})"):
                    sentiment = "👍 推荐" if review['voted_up'] else "👎 不推荐"
                    st.write(f"**{sentiment}**")
                    st.write(review['review'][:800])


# Streamlit page config would go in the main dashboard.py
# This module is imported and called from there

