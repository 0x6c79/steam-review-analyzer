#!/usr/bin/env python3
"""
Keyword & Topic Extraction Module
Extracts common keywords, topics, and themes from reviews
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import numpy as np
from collections import Counter
from typing import Dict, List, Tuple
import re

class KeywordAndTopicExtractor:
    """Extract keywords and topics from reviews"""
    
    # Common English stop words (expanded)
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'be', 'been', 'being',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who',
        'this', 'that', 'these', 'those', 'my', 'your', 'his', 'her', 'its',
        'just', 'only', 'not', 'no', 'can', 'could', 'would', 'should', 'may',
        'might', 'will', 'have', 'has', 'had', 'do', 'does', 'did', 'get', 'got',
        'if', 'then', 'when', 'where', 'why', 'how', 'all', 'each', 'every',
        'about', 'so', 'as', 'game', 'review', 'play', 'playing', 'played'
    }
    
    # Common Chinese stop words
    CHINESE_STOP_WORDS = {
        '的', '一', '是', '在', '不', '了', '有', '和', '人', '这', '中',
        '大', '为', '上', '个', '国', '我', '以', '要', '他', '时', '来',
        '用', '们', '生', '到', '作', '地', '于', '出', '就', '分', '对',
        '成', '会', '可', '主', '发', '年', '动', '同', '工', '也', '能',
        '下', '现', '山', '民', '候', '经', '十', '反', '问', '很', '把',
        '她', '为', '只', '又', '多', '天', '比', '高', '自', '二', '而',
        '已', '其', '挺', '真', '的', '很', '游戏', '玩', '好', '还'
    }
    
    def __init__(self, df: pd.DataFrame, language: str = 'english'):
        """Initialize extractor"""
        self.df = df.copy()
        self.language = language
        self.stop_words = self.STOP_WORDS if language == 'english' else self.CHINESE_STOP_WORDS
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Convert to lowercase
        text = str(text).lower()
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s\u4e00-\u9fff]', ' ', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        if self.language == 'english':
            words = text.split()
            # Filter short words and stop words
            return [w for w in words if len(w) > 2 and w not in self.stop_words]
        else:
            # For Chinese, use simple character-based tokenization
            # In production, would use jieba or similar
            import jieba
            words = jieba.cut(text)
            return [w for w in words if w not in self.CHINESE_STOP_WORDS and len(w) > 0]
    
    def extract_keywords(self, top_n: int = 50, min_length: int = 3) -> Dict:
        """
        Extract most common keywords from reviews
        """
        all_keywords = []
        
        for review in self.df['review'].astype(str):
            clean_text = self._clean_text(review)
            keywords = self._tokenize(clean_text)
            all_keywords.extend(keywords)
        
        # Count frequency
        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(top_n)
        
        return {
            'keywords': {word: count for word, count in top_keywords},
            'keyword_list': [word for word, _ in top_keywords],
            'total_unique': len(keyword_counts),
            'average_frequency': np.mean([count for _, count in top_keywords])
        }
    
    def extract_bigrams(self, top_n: int = 30) -> Dict:
        """
        Extract most common two-word phrases (bigrams)
        """
        bigrams = []
        
        for review in self.df['review'].astype(str):
            clean_text = self._clean_text(review)
            tokens = self._tokenize(clean_text)
            
            # Create bigrams
            for i in range(len(tokens) - 1):
                bigram = f"{tokens[i]} {tokens[i+1]}"
                bigrams.append(bigram)
        
        bigram_counts = Counter(bigrams)
        top_bigrams = bigram_counts.most_common(top_n)
        
        return {
            'bigrams': {phrase: count for phrase, count in top_bigrams},
            'top_phrases': [phrase for phrase, _ in top_bigrams],
            'frequency': {phrase: count for phrase, count in top_bigrams}
        }
    
    def extract_topics(self, num_topics: int = 5) -> Dict:
        """
        Extract main topics/themes from reviews using keyword clustering
        """
        topic_keywords = {
            'Gameplay & Mechanics': ['gameplay', 'mechanic', 'control', 'balance', 'difficulty',
                                    '游戏', '机制', '难度', '平衡'],
            'Graphics & Visual': ['graphics', 'visual', 'graphics card', 'resolution', 'texture',
                                '画面', '画质', '分辨率', '贴图'],
            'Performance & Tech': ['performance', 'lag', 'fps', 'crash', 'bug', 'glitch',
                                 '性能', '卡顿', '帧率', '崩溃', '漏洞'],
            'Story & Content': ['story', 'plot', 'narrative', 'character', 'mission', 'quest',
                              '故事', '剧情', '任务', '角色'],
            'Sound & Music': ['sound', 'audio', 'music', 'voice', 'voice act',
                            '声音', '音乐', '配音'],
            'Multiplayer & Online': ['multiplayer', 'online', 'pvp', 'co-op', 'server',
                                   '多人', '联网', '服务器'],
            'Price & Value': ['price', 'expensive', 'worth', 'value', 'dlc', 'money',
                            '价格', '值得', '花费', '金钱'],
            'Learning Curve': ['difficulty', 'learning', 'complex', 'intuitive', 'beginner',
                             '难度', '学习', '复杂', '新手'],
            'Replayability': ['replay', 'replay value', 'content length', 'grinding',
                            '重玩', '内容', '时长'],
            'Community & Support': ['community', 'support', 'developer', 'update', 'mod',
                                  '社区', '更新', '开发者']
        }
        
        topic_scores = {topic: 0 for topic in topic_keywords.keys()}
        
        for review in self.df['review'].astype(str):
            clean_text = self._clean_text(review)
            for topic, keywords in topic_keywords.items():
                count = sum(1 for keyword in keywords if keyword in clean_text)
                if count > 0:
                    topic_scores[topic] += count
        
        # Sort by score
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'topics': {topic: score for topic, score in sorted_topics[:num_topics]},
            'percentages': {topic: f"{score/sum(topic_scores.values())*100:.1f}%" 
                          for topic, score in sorted_topics[:num_topics]},
            'all_topics': dict(sorted_topics)
        }
    
    def sentiment_by_topic(self) -> Dict:
        """
        Analyze sentiment for each major topic
        """
        topics_to_analyze = {
            'Gameplay': ['gameplay', 'mechanic', 'control', '游戏', '机制'],
            'Graphics': ['graphics', 'visual', '画面', '画质'],
            'Performance': ['lag', 'fps', 'crash', '卡顿', '崩溃'],
            'Story': ['story', 'plot', '故事', '剧情'],
            'Price': ['price', 'expensive', '价格', '昂贵']
        }
        
        sentiment_by_topic = {}
        
        for topic, keywords in topics_to_analyze.items():
            # Find reviews mentioning this topic
            mask = self.df['review'].astype(str).str.lower().str.contains('|'.join(keywords), na=False)
            if mask.sum() > 0:
                topic_reviews = self.df[mask]
                positive_rate = topic_reviews['voted_up'].mean() * 100
                sentiment_by_topic[topic] = {
                    'review_count': int(mask.sum()),
                    'positive_rate': round(positive_rate, 1),
                    'percentage_of_total': f"{mask.sum()/len(self.df)*100:.1f}%"
                }
        
        return sentiment_by_topic
    
    def generate_word_cloud_data(self, top_n: int = 100) -> List[Dict]:
        """
        Generate data suitable for word cloud visualization
        """
        keywords = self.extract_keywords(top_n=top_n)['keywords']
        
        # Normalize sizes for word cloud (1-100)
        max_freq = max(keywords.values())
        min_freq = min(keywords.values())
        
        word_cloud_data = []
        for word, freq in keywords.items():
            size = 1 + (freq - min_freq) / (max_freq - min_freq) * 99
            word_cloud_data.append({
                'word': word,
                'size': int(size),
                'frequency': int(freq)
            })
        
        return word_cloud_data


def extract_all_keywords_and_topics(df: pd.DataFrame) -> Dict:
    """
    Complete keyword and topic extraction
    """
    # Detect language based on content
    sample_text = ' '.join(df['review'].astype(str).head(100))
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in sample_text)
    language = 'chinese' if has_chinese else 'english'
    
    extractor = KeywordAndTopicExtractor(df, language=language)
    
    results = {
        'keywords': extractor.extract_keywords(),
        'bigrams': extractor.extract_bigrams(),
        'topics': extractor.extract_topics(),
        'sentiment_by_topic': extractor.sentiment_by_topic(),
        'word_cloud_data': extractor.generate_word_cloud_data()
    }
    
    return results


if __name__ == '__main__':
    # Example usage
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        df = pd.read_csv(csv_file)
        results = extract_all_keywords_and_topics(df)
        import json
        print(json.dumps(results, indent=2, ensure_ascii=False))
