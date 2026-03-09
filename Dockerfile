FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml .
COPY src src/

RUN uv pip install --system -e ".[dev]"

RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('vader_lexicon')"

ENV PYTHONPATH=/app/src

EXPOSE 8000 8501

CMD ["uvicorn", "src.steam_review.api.api:app", "--host", "0.0.0.0", "--port", "8000"]
