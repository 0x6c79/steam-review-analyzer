import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

try:
    from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
    from sklearn.decomposition import LatentDirichletAllocation, NMF
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn not available, topic modeling disabled")


class TopicModeler:
    def __init__(self, n_topics: int = 10, method: str = "lda"):
        self.n_topics = n_topics
        self.method = method
        self.vectorizer = None
        self.model = None
        self.feature_names = None
        
    def _preprocess_text(self, text: str, lang: str = 'en') -> str:
        import utils
        tokens = utils.preprocess_text(text, lang)
        return ' '.join(tokens)
    
    def fit(self, texts: List[str], lang: str = 'en') -> 'TopicModeler':
        if not SKLEARN_AVAILABLE:
            logger.error("sklearn not available")
            return self
            
        try:
            processed_texts = [self._preprocess_text(t, lang) for t in texts]
            processed_texts = [t for t in processed_texts if t.strip()]
            
            if len(processed_texts) < 10:
                logger.warning("Not enough texts for topic modeling")
                return self
            
            if self.method == "lda":
                self.vectorizer = CountVectorizer(
                    max_df=0.95,
                    min_df=2,
                    max_features=1000
                )
                doc_term_matrix = self.vectorizer.fit_transform(processed_texts)
                
                self.model = LatentDirichletAllocation(
                    n_components=self.n_topics,
                    random_state=42,
                    max_iter=10,
                    learning_method='online'
                )
            else:
                self.vectorizer = TfidfVectorizer(
                    max_df=0.95,
                    min_df=2,
                    max_features=1000
                )
                tfidf_matrix = self.vectorizer.fit_transform(processed_texts)
                
                self.model = NMF(
                    n_components=self.n_topics,
                    random_state=42,
                    max_iter=200
                )
            
            self.model.fit(tfidf_matrix if self.method == "nmf" else doc_term_matrix)
            self.feature_names = self.vectorizer.get_feature_names_out()
            
            logger.info(f"Topic model trained with {self.n_topics} topics")
            
        except Exception as e:
            logger.error(f"Topic modeling failed: {e}")
        
        return self
    
    def get_topics(self, n_words: int = 10) -> List[List[Tuple[str, float]]]:
        if not self.model or not self.feature_names:
            return []
        
        topics = []
        for topic_idx, topic in enumerate(self.model.components_):
            top_words = [
                (self.feature_names[i], topic[i])
                for i in topic.argsort()[:-n_words - 1:-1]
            ]
            topics.append(top_words)
        
        return topics
    
    def get_document_topics(self, texts: List[str], lang: str = 'en') -> np.ndarray:
        if not self.model or not self.vectorizer:
            return np.zeros((len(texts), self.n_topics))
        
        processed_texts = [self._preprocess_text(t, lang) for t in texts]
        
        try:
            doc_term_matrix = self.vectorizer.transform(processed_texts)
            return self.model.transform(doc_term_matrix)
        except:
            return np.zeros((len(texts), self.n_topics))


def analyze_topics(df: pd.DataFrame, n_topics: int = 10, method: str = "lda") -> Dict:
    if not SKLEARN_AVAILABLE:
        return {"error": "sklearn not available"}
    
    logger.info(f"Performing topic modeling with {n_topics} topics")
    
    df_filtered = df.dropna(subset=['review']).copy()
    df_filtered = df_filtered[df_filtered['review'].astype(str).str.len() > 20]
    
    if df_filtered.empty:
        return {"error": "No valid reviews for topic modeling"}
    
    lang = df_filtered['detected_language'].mode().iloc[0] if 'detected_language' in df_filtered.columns else 'en'
    
    texts = df_filtered['review'].astype(str).tolist()
    
    modeler = TopicModeler(n_topics=n_topics, method=method)
    modeler.fit(texts, lang)
    
    topics = modeler.get_topics(n_words=10)
    
    topic_labels = []
    for i, topic in enumerate(topics):
        words = [w[0] for w in topic[:5]]
        topic_labels.append(f"Topic {i+1}: {', '.join(words)}")
    
    doc_topics = modeler.get_document_topics(texts, lang)
    df_filtered['dominant_topic'] = doc_topics.argmax(axis=1)
    
    topic_counts = df_filtered['dominant_topic'].value_counts().to_dict()
    
    positive_topics = df_filtered[df_filtered['voted_up']]['dominant_topic'].value_counts()
    negative_topics = df_filtered[~df_filtered['voted_up']]['dominant_topic'].value_counts()
    
    return {
        "topics": [
            {
                "id": i,
                "label": topic_labels[i],
                "words": [{"word": w, "weight": float(s)} for w, s in topics[i]],
                "count": topic_counts.get(i, 0),
                "positive_ratio": positive_topics.get(i, 0) / max(topic_counts.get(i, 1), 1),
            }
            for i in range(len(topics))
        ],
        "document_topics": doc_topics.tolist()[:100]
    }
