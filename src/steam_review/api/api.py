import os
import sys

# Add project root to path for both module and direct execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
from src.steam_review.storage.database import get_database
from src.steam_review import config

config.setup_logging()

app = FastAPI(
    title="Steam Review Analysis API",
    description="API for analyzing Steam game reviews",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Review(BaseModel):
    recommendation_id: str
    app_id: Optional[str] = None
    language: Optional[str] = None
    review: Optional[str] = None
    voted_up: bool
    timestamp_created: int


class Stats(BaseModel):
    total: int
    positive: int
    negative: int
    positive_rate: float


@app.get("/")
async def root():
    return {"message": "Steam Review Analysis API", "version": "1.0.0"}


@app.get("/reviews", response_model=List[Review])
async def get_reviews(
    app_id: Optional[str] = Query(None, description="Filter by App ID"),
    limit: int = Query(10, ge=1, le=1000, description="Number of reviews to return"),
    language: Optional[str] = Query(None, description="Filter by language")
):
    db = get_database()
    df = db.get_reviews(app_id, limit * 2)
    
    if language:
        df = df[df['language'] == language]
    
    df = df.head(limit)
    
    return df.to_dict(orient='records')


@app.get("/reviews/{recommendation_id}")
async def get_review(recommendation_id: str):
    db = get_database()
    df = db.get_reviews()
    
    review = df[df['recommendation_id'] == recommendation_id]
    if review.empty:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return review.to_dict(orient='records')[0]


@app.get("/stats", response_model=Stats)
async def get_stats(app_id: Optional[str] = Query(None, description="Filter by App ID")):
    db = get_database()
    stats = db.get_stats(app_id)
    
    positive_rate = 0.0
    if stats['total'] > 0:
        positive_rate = stats['positive'] / stats['total'] * 100
    
    return Stats(
        total=stats['total'],
        positive=stats['positive'],
        negative=stats['negative'],
        positive_rate=round(positive_rate, 2)
    )


@app.get("/languages")
async def get_languages(app_id: Optional[str] = Query(None, description="Filter by App ID")):
    db = get_database()
    df = db.get_reviews(app_id)
    
    lang_counts = df['language'].value_counts().to_dict()
    return {"languages": lang_counts}


@app.get("/export/{format}")
async def export_reviews(
    format: str,
    app_id: Optional[str] = Query(None, description="Filter by App ID")
):
    from fastapi.responses import FileResponse
    import tempfile
    import os
    
    db = get_database()
    
    if format == 'csv':
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            db.export_to_csv(f.name, app_id)
            return FileResponse(f.name, media_type='text/csv', filename='reviews.csv')
    
    elif format == 'excel':
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            db.export_to_excel(f.name, app_id)
            return FileResponse(f.name, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename='reviews.xlsx')
    
    elif format == 'json':
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            db.export_to_json(f.name, app_id)
            return FileResponse(f.name, media_type='application/json', filename='reviews.json')
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
