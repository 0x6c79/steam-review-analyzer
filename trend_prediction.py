import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn not available, trend prediction disabled")


class TrendPredictor:
    def __init__(self, forecast_days: int = 30):
        self.forecast_days = forecast_days
        self.model = None
        self.poly = None
        self.scaler_mean = None
        self.scaler_std = None
        
    def _prepare_data(self, df: pd.DataFrame, freq: str = 'W') -> pd.DataFrame:
        if 'timestamp_created' in df.columns:
            df = df.set_index('timestamp_created')
        elif not isinstance(df.index, pd.DatetimeIndex):
            logger.warning("No datetime index found")
            return pd.DataFrame()
        
        df = df.sort_index()
        
        if freq == 'D':
            period = 'D'
        elif freq == 'W':
            period = 'W'
        else:
            period = 'M'
        
        grouped = df.resample(period).agg({
            'voted_up': ['sum', 'count', 'mean'],
            'review_length': 'mean',
            'sentiment_score': 'mean' if 'sentiment_score' in df.columns else 'count'
        })
        
        grouped.columns = ['positive', 'total', 'positive_rate', 'avg_length', 'avg_sentiment']
        grouped['negative'] = grouped['total'] - grouped['positive']
        grouped = grouped.fillna(0)
        
        return grouped
    
    def fit_predict(self, df: pd.DataFrame, freq: str = 'W') -> Dict:
        if not SKLEARN_AVAILABLE:
            return {"error": "sklearn not available"}
        
        try:
            data = self._prepare_data(df, freq)
            
            if len(data) < 4:
                return {"error": "Not enough data for prediction (minimum 4 periods)"}
            
            X = np.arange(len(data)).reshape(-1, 1)
            y = data['positive_rate'].values
            
            self.poly = PolynomialFeatures(degree=2)
            X_poly = self.poly.fit_transform(X)
            
            self.model = LinearRegression()
            self.model.fit(X_poly, y)
            
            future_X = np.arange(len(data), len(data) + self.forecast_days).reshape(-1, 1)
            future_X_poly = self.poly.transform(future_X)
            predictions = self.model.predict(future_X_poly)
            predictions = np.clip(predictions, 0, 1)
            
            last_date = data.index[-1]
            if freq == 'D':
                future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=self.forecast_days, freq='D')
            elif freq == 'W':
                future_dates = pd.date_range(start=last_date + timedelta(weeks=1), periods=self.forecast_days, freq='W')
            else:
                future_dates = pd.date_range(start=last_date + timedelta(days=30), periods=self.forecast_days, freq='M')
            
            return {
                "historical": {
                    "dates": data.index.strftime('%Y-%m-%d').tolist(),
                    "positive_rate": data['positive_rate'].tolist(),
                    "total_reviews": data['total'].tolist()
                },
                "forecast": {
                    "dates": future_dates.strftime('%Y-%m-%d').tolist(),
                    "predicted_rate": predictions.tolist()
                },
                "trend": self._calculate_trend(predictions),
                "statistics": {
                    "current_rate": float(data['positive_rate'].iloc[-1]),
                    "average_rate": float(data['positive_rate'].mean()),
                    "volatility": float(data['positive_rate'].std()),
                    "total_reviews": int(data['total'].sum())
                }
            }
            
        except Exception as e:
            logger.error(f"Trend prediction failed: {e}")
            return {"error": str(e)}
    
    def _calculate_trend(self, predictions: np.ndarray) -> str:
        if len(predictions) < 2:
            return "stable"
        
        first_half = predictions[:len(predictions)//2].mean()
        second_half = predictions[len(predictions)//2:].mean()
        
        diff = second_half - first_half
        
        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"


def analyze_trends(df: pd.DataFrame, forecast_days: int = 30) -> Dict:
    logger.info("Analyzing review trends and making predictions")
    
    predictor = TrendPredictor(forecast_days=forecast_days)
    return predictor.fit_predict(df, freq='W')


def detect_anomalies(df: pd.DataFrame, window: int = 7, threshold: float = 2.0) -> List[Dict]:
    logger.info("Detecting anomalies in review patterns")
    
    data = df.set_index('timestamp_created') if 'timestamp_created' in df.columns else df
    
    daily = data.resample('D').agg({
        'voted_up': ['sum', 'count', 'mean']
    })
    daily.columns = ['positive', 'total', 'rate']
    daily = daily.fillna(0)
    
    if len(daily) < window * 2:
        return [{"error": "Not enough data for anomaly detection"}]
    
    daily['rate_ma'] = daily['rate'].rolling(window=window).mean()
    daily['rate_std'] = daily['rate'].rolling(window=window).std()
    daily['z_score'] = (daily['rate'] - daily['rate_ma']) / daily['rate_std']
    
    anomalies = daily[daily['z_score'].abs() > threshold]
    
    results = []
    for date, row in anomalies.iterrows():
        results.append({
            "date": date.strftime('%Y-%m-%d'),
            "positive_rate": float(row['rate']),
            "moving_average": float(row['rate_ma']),
            "z_score": float(row['z_score']),
            "type": "spike" if row['z_score'] > 0 else "drop"
        })
    
    return results
