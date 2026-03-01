import logging
from typing import Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available, falling back to VADER")


class AdvancedSentimentAnalyzer:
    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment"):
        self.model_name = model_name
        self.analyzer = None
        self.tokenizer = None
        
    def load_model(self):
        if not TRANSFORMERS_AVAILABLE:
            return False
        
        try:
            logger.info(f"Loading sentiment model: {self.model_name}")
            self.analyzer = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                tokenizer=self.model_name,
                device=-1,
                truncation=True,
                max_length=512
            )
            logger.info("Sentiment model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load sentiment model: {e}")
            return False
    
    def analyze(self, text: str) -> dict:
        if not self.analyzer:
            return {"label": "NEUTRAL", "score": 0.5, "compound": 0.0}
        
        try:
            text = str(text)[:512]
            result = self.analyzer(text)[0]
            
            label = result['label'].lower()
            score = result['score']
            
            compound = 0.0
            if label == 'positive':
                compound = score
            elif label == 'negative':
                compound = -score
            else:
                compound = 0.0
                
            return {
                "label": label,
                "score": score,
                "compound": compound
            }
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return {"label": "NEUTRAL", "score": 0.5, "compound": 0.0}
    
    def analyze_batch(self, texts: list) -> list:
        if not self.analyzer:
            return [{"label": "NEUTRAL", "score": 0.5, "compound": 0.0}] * len(texts)
        
        results = []
        batch_size = 32
        
        for i in range(0, len(texts), batch_size):
            batch = [str(t)[:512] for t in texts[i:i+batch_size]]
            try:
                batch_results = self.analyzer(batch)
                for result in batch_results:
                    label = result['label'].lower()
                    score = result['score']
                    compound = score if label == 'positive' else (-score if label == 'negative' else 0.0)
                    results.append({
                        "label": label,
                        "score": score,
                        "compound": compound
                    })
            except Exception as e:
                logger.warning(f"Batch analysis failed: {e}")
                results.extend([{"label": "NEUTRAL", "score": 0.5, "compound": 0.0}] * len(batch))
        
        return results


def analyze_sentiment_advanced(df: pd.DataFrame, use_advanced: bool = True) -> pd.DataFrame:
    df = df.copy()
    
    if use_advanced and TRANSFORMERS_AVAILABLE:
        logger.info("Using advanced BERT-based sentiment analysis")
        analyzer = AdvancedSentimentAnalyzer()
        if analyzer.load_model():
            texts = df['review'].fillna('').tolist()
            results = analyzer.analyze_batch(texts)
            
            df['sentiment_label'] = [r['label'] for r in results]
            df['sentiment_score'] = [r['compound'] for r in results]
            df['sentiment_confidence'] = [r['score'] for r in results]
        else:
            logger.warning("Failed to load advanced model, using VADER")
            use_advanced = False
    
    if not use_advanced or 'sentiment_score' not in df.columns:
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        import nltk
        
        try:
            nltk.data.find('sentiment/vader_lexicon')
        except:
            nltk.download('vader_lexicon')
        
        analyzer = SentimentIntensityAnalyzer()
        
        def get_vader_sentiment(text):
            try:
                vs = analyzer.polarity_scores(str(text))
                return vs['compound']
            except:
                return 0.0
        
        df['sentiment_score'] = df.apply(
            lambda row: get_vader_sentiment(row['review']) 
            if row.get('detected_language') == 'en' 
            else (1 if row.get('voted_up') else 0), 
            axis=1
        )
        df['sentiment_label'] = df['sentiment_score'].apply(
            lambda x: 'positive' if x > 0.05 else ('negative' if x < -0.05 else 'neutral')
        )
        df['sentiment_confidence'] = df['sentiment_score'].abs()
    
    return df
