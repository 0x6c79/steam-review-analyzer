import sqlite3
import pandas as pd
import logging
from src.steam_review import config
from src.steam_review.utils.exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


class ReviewDatabase:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = config.DB_PATH
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
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
            """)
            # Enhanced indexing strategy for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_app_id ON reviews(app_id)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON reviews(timestamp_created)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_voted_up ON reviews(voted_up)")
            # Additional indexes for filtering and sorting
            conn.execute("CREATE INDEX IF NOT EXISTS idx_language ON reviews(language)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_detected_language ON reviews(detected_language)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_playtime ON reviews(playtime_forever)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sentiment ON reviews(sentiment_score)"
            )
            # Composite indexes for common queries
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_app_timestamp ON reviews(app_id, timestamp_created)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_app_voted ON reviews(app_id, voted_up)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_app_language ON reviews(app_id, language)"
            )
            logger.info(f"Database initialized at {self.db_path}")

    def insert_reviews(self, df):
        if df.empty:
            logger.warning("No reviews to insert")
            return 0

        df = df.copy()
        df["scraped_at"] = pd.Timestamp.now()

        # Handle duplicate columns
        if "recommendationid" in df.columns and "recommendation_id" in df.columns:
            df = df.drop(columns=["recommendationid"])
        elif "recommendationid" in df.columns:
            df = df.rename(columns={"recommendationid": "recommendation_id"})

        # Handle app_id column naming
        if "appid" in df.columns and "app_id" not in df.columns:
            df = df.rename(columns={"appid": "app_id"})

        existing_ids = self.get_existing_ids()
        # Convert to string for comparison to handle int vs string mismatch
        df["recommendation_id"] = df["recommendation_id"].astype(str)
        new_reviews = df[~df["recommendation_id"].isin(existing_ids)]

        if new_reviews.empty:
            logger.info("No new reviews to insert")
            return 0

        columns = [c for c in new_reviews.columns if c in self.get_table_columns()]

        with sqlite3.connect(self.db_path) as conn:
            new_reviews[columns].to_sql(
                "reviews", conn, if_exists="append", index=False
            )

        logger.info(f"Inserted {len(new_reviews)} new reviews into database")
        return len(new_reviews)

    def get_existing_ids(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql("SELECT recommendation_id FROM reviews", conn)
                return set(df["recommendation_id"].tolist())
        except:
            return set()

    def get_table_columns(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("PRAGMA table_info(reviews)")
            return {row[1] for row in cursor.fetchall()}

    def get_reviews(
        self,
        app_id=None,
        limit=None,
        start_date=None,
        end_date=None,
        min_playtime=None,
        max_playtime=None,
        language=None,
        sentiment_min=None,
        sentiment_max=None,
        voted_up_only=None,
    ):
        """
        Get reviews with advanced filtering options.

        Args:
            app_id: Filter by app ID
            limit: Maximum number of reviews to return
            start_date: Start timestamp (Unix epoch or datetime)
            end_date: End timestamp (Unix epoch or datetime)
            min_playtime: Minimum playtime in hours
            max_playtime: Maximum playtime in hours
            language: Filter by language code
            sentiment_min: Minimum sentiment score (0-1)
            sentiment_max: Maximum sentiment score (0-1)
            voted_up_only: If True, only return positive reviews
        """
        query = "SELECT * FROM reviews WHERE 1=1"
        params = []

        # App ID filter
        if app_id:
            query += " AND app_id = ?"
            params.append(str(app_id))

        # Date range filters
        if start_date:
            if isinstance(start_date, pd.Timestamp):
                start_timestamp = int(start_date.timestamp())
            else:
                start_timestamp = start_date
            query += " AND timestamp_created >= ?"
            params.append(start_timestamp)

        if end_date:
            if isinstance(end_date, pd.Timestamp):
                end_timestamp = int(end_date.timestamp())
            else:
                end_timestamp = end_date
            query += " AND timestamp_created <= ?"
            params.append(end_timestamp)

        # Playtime filters
        if min_playtime is not None:
            query += " AND playtime_forever >= ?"
            params.append(min_playtime)

        if max_playtime is not None:
            query += " AND playtime_forever <= ?"
            params.append(max_playtime)

        # Language filter
        if language:
            query += " AND (language = ? OR detected_language = ?)"
            params.append(language)
            params.append(language)

        # Sentiment range filter
        if sentiment_min is not None:
            query += " AND sentiment_score >= ?"
            params.append(sentiment_min)

        if sentiment_max is not None:
            query += " AND sentiment_score <= ?"
            params.append(sentiment_max)

        # Voted up filter
        if voted_up_only is not None:
            query += " AND voted_up = ?"
            params.append(1 if voted_up_only else 0)

        query += " ORDER BY timestamp_created DESC"

        if limit:
            query += f" LIMIT {limit}"

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql(query, conn, params=params)

        # Clean up data types for Streamlit Arrow compatibility
        if not df.empty:
            # Fix timestamp columns
            for col in ["timestamp_created", "timestamp_updated"]:
                if col in df.columns:
                    # Convert to numeric, handling string representations like 'False'
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # Fix boolean columns
            for col in ["voted_up", "is_recommended"]:
                if col in df.columns:
                    if df[col].dtype == "object":
                        # Convert string representations to boolean/int
                        def convert_bool(x):
                            if isinstance(x, bool):
                                return 1 if x else 0
                            if x in (1, "1", "True"):
                                return 1
                            return 0

                        df[col] = df[col].apply(convert_bool)
                        # Fill any remaining NaN with 0
                        df[col] = df[col].fillna(0).astype(int)

            # Drop columns with all None/NaN values to avoid Arrow conversion issues
            df = df.dropna(axis=1, how="all")

        return df

    def get_stats(self, app_id=None, start_date=None, end_date=None):
        """Get statistics with optional filtering."""
        query = (
            "SELECT COUNT(*) as total, SUM(voted_up) as positive FROM reviews WHERE 1=1"
        )
        params = []
        if app_id:
            query += " AND app_id = ?"
            params.append(str(app_id))

        if start_date:
            if isinstance(start_date, pd.Timestamp):
                start_timestamp = int(start_date.timestamp())
            else:
                start_timestamp = start_date
            query += " AND timestamp_created >= ?"
            params.append(start_timestamp)

        if end_date:
            if isinstance(end_date, pd.Timestamp):
                end_timestamp = int(end_date.timestamp())
            else:
                end_timestamp = end_date
            query += " AND timestamp_created <= ?"
            params.append(end_timestamp)

        with sqlite3.connect(self.db_path) as conn:
            result = pd.read_sql(query, conn, params=params).iloc[0]
            return {
                "total": result["total"],
                "positive": int(result["positive"])
                if pd.notna(result["positive"])
                else 0,
                "negative": int(result["total"] - result["positive"])
                if pd.notna(result["positive"])
                else 0,
            }

    def get_available_languages(self, app_id=None):
        """Get list of unique languages in the database."""
        query = "SELECT DISTINCT language FROM reviews WHERE 1=1"
        params = []
        if app_id:
            query += " AND app_id = ?"
            params.append(str(app_id))
        query += " ORDER BY language"

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql(query, conn, params=params)
        return df["language"].dropna().unique().tolist() if not df.empty else []

    def get_date_range(self, app_id=None):
        """Get min and max dates in the database."""
        query = "SELECT MIN(timestamp_created) as min_date, MAX(timestamp_created) as max_date FROM reviews WHERE 1=1"
        params = []
        if app_id:
            query += " AND app_id = ?"
            params.append(str(app_id))

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql(query, conn, params=params)

        if not df.empty:
            row = df.iloc[0]
            return {
                "min": pd.Timestamp(row["min_date"], unit="s")
                if row["min_date"]
                else None,
                "max": pd.Timestamp(row["max_date"], unit="s")
                if row["max_date"]
                else None,
            }
        return {"min": None, "max": None}

    def get_playtime_range(self, app_id=None):
        """Get min and max playtime values."""
        query = "SELECT MIN(playtime_forever) as min_pt, MAX(playtime_forever) as max_pt FROM reviews WHERE 1=1"
        params = []
        if app_id:
            query += " AND app_id = ?"
            params.append(str(app_id))

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql(query, conn, params=params)

        if not df.empty:
            row = df.iloc[0]
            return {
                "min": row["min_pt"] if row["min_pt"] else 0,
                "max": row["max_pt"] if row["max_pt"] else 0,
            }
        return {"min": 0, "max": 0}

    def get_all_games(self):
        """Get all games in database with their stats."""
        query = """
            SELECT 
                app_id,
                COUNT(*) as total,
                SUM(voted_up) as positive,
                COUNT(*) - SUM(voted_up) as negative
            FROM reviews
            GROUP BY app_id
            ORDER BY total DESC
        """
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql(query, conn)

        games = []
        for _, row in df.iterrows():
            games.append(
                {
                    "app_id": row["app_id"],
                    "total": int(row["total"]),
                    "positive": int(row["positive"])
                    if pd.notna(row["positive"])
                    else 0,
                    "negative": int(row["negative"])
                    if pd.notna(row["negative"])
                    else 0,
                }
            )
        return games

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
        df.to_json(json_path, orient="records", force_ascii=False, indent=2)
        logger.info(f"Exported {len(df)} reviews to {json_path}")


def get_database(db_path=None):
    return ReviewDatabase(db_path)
