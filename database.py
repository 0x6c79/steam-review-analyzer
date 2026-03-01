import sqlite3
import pandas as pd
import logging
import os
import config

logger = logging.getLogger(__name__)


class ReviewDatabase:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(config.BASE_DIR, 'reviews.db')
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    recommendation_id TEXT PRIMARY KEY,
                    app_id TEXT,
                    language TEXT,
                    review TEXT,
                    timestamp_created INTEGER,
                    timestamp_updated INTEGER,
                    voted_up INTEGER,
                    playtime_forever REAL,
                    playtime_last_two_weeks REAL,
                    author_steam_id TEXT,
                    author_num_games_owned INTEGER,
                    author_num_reviews INTEGER,
                    author_playtime_forever REAL,
                    written_during_early_access INTEGER,
                    detected_language TEXT,
                    sentiment_score REAL,
                    review_length INTEGER,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_app_id ON reviews(app_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON reviews(timestamp_created)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_voted_up ON reviews(voted_up)')
            logger.info(f"Database initialized at {self.db_path}")
    
    def insert_reviews(self, df):
        if df.empty:
            logger.warning("No reviews to insert")
            return 0
        
        df = df.copy()
        df['scraped_at'] = pd.Timestamp.now()
        
        if 'recommendationid' in df.columns:
            df = df.rename(columns={'recommendationid': 'recommendation_id'})
        
        existing_ids = self.get_existing_ids()
        new_reviews = df[~df['recommendation_id'].isin(existing_ids)]
        
        if new_reviews.empty:
            logger.info("No new reviews to insert")
            return 0
        
        columns = [c for c in new_reviews.columns if c in self.get_table_columns()]
        
        with sqlite3.connect(self.db_path) as conn:
            new_reviews[columns].to_sql('reviews', conn, if_exists='append', index=False)
        
        logger.info(f"Inserted {len(new_reviews)} new reviews into database")
        return len(new_reviews)
    
    def get_existing_ids(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql('SELECT recommendation_id FROM reviews', conn)
                return set(df['recommendation_id'].tolist())
        except:
            return set()
    
    def get_table_columns(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('PRAGMA table_info(reviews)')
            return {row[1] for row in cursor.fetchall()}
    
    def get_reviews(self, app_id=None, limit=None):
        query = 'SELECT * FROM reviews'
        params = []
        if app_id:
            query += ' WHERE app_id = ?'
            params.append(str(app_id))
        query += ' ORDER BY timestamp_created DESC'
        if limit:
            query += f' LIMIT {limit}'
        
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql(query, conn, params=params)
    
    def get_stats(self, app_id=None):
        query = 'SELECT COUNT(*) as total, SUM(voted_up) as positive FROM reviews'
        params = []
        if app_id:
            query += ' WHERE app_id = ?'
            params.append(str(app_id))
        
        with sqlite3.connect(self.db_path) as conn:
            result = pd.read_sql(query, conn, params=params).iloc[0]
            return {
                'total': result['total'],
                'positive': int(result['positive']) if pd.notna(result['positive']) else 0,
                'negative': int(result['total'] - result['positive']) if pd.notna(result['positive']) else 0
            }
    
    def export_to_csv(self, csv_path, app_id=None):
        df = self.get_reviews(app_id)
        df.to_csv(csv_path, index=False)
        logger.info(f"Exported {len(df)} reviews to {csv_path}")
    
    def export_to_excel(self, excel_path, app_id=None):
        df = self.get_reviews(app_id)
        df.to_excel(excel_path, index=False)
        logger.info(f"Exported {len(df)} reviews to {excel_path}")
    
    def export_to_json(self, json_path, app_id=None):
        df = self.get_reviews(app_id)
        df.to_json(json_path, orient='records', force_ascii=False, indent=2)
        logger.info(f"Exported {len(df)} reviews to {json_path}")


def get_database(db_path=None):
    return ReviewDatabase(db_path)
