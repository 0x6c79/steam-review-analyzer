"""
Advanced Sentiment Analysis Module
- Multi-language support
- Aspect-Based Sentiment Analysis (ABSA)
- Multi-dimensional emotion detection
- Sarcasm and toxicity detection
"""

import logging
from enum import Enum
from typing import Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

TRANSFORMERS_AVAILABLE = False
TRY_IMPORT_TRANSFORMERS = True

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    from transformers import AutoModelForTokenClassification

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRY_IMPORT_TRANSFORMERS = False
    logger.warning("transformers not available, using fallback methods")


class SentimentType(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class EmotionType(Enum):
    JOY = "joy"
    ANGER = "anger"
    SADNESS = "sadness"
    FEAR = "fear"
    SURPRISE = "surprise"
    ANTICIPATION = "anticipation"
    DISGUST = "disgust"
    TRUST = "trust"


ASPECT_KEYWORDS = {
    "gameplay": [
        "gameplay",
        "mechanic",
        "control",
        "combat",
        "puzzle",
        "level",
        "difficulty",
        "fun",
        "玩法",
        "机制",
        "操作",
        "关卡",
        "难度",
    ],
    "graphics": [
        "graphics",
        "graphic",
        "visual",
        "art",
        "texture",
        "model",
        "effect",
        "画面",
        "画质",
        "美术",
        "特效",
        "图形",
    ],
    "audio": [
        "sound",
        "music",
        "bgm",
        "voice",
        "audio",
        "音效",
        "音乐",
        "配音",
        "声音",
    ],
    "story": [
        "story",
        "narrative",
        "plot",
        "character",
        "lore",
        "剧情",
        "故事",
        "角色",
        "叙事",
    ],
    "performance": [
        "performance",
        "fps",
        "frame",
        "lag",
        "bug",
        "crash",
        "optimization",
        "性能",
        "帧率",
        "优化",
        "bug",
    ],
    "price": [
        "price",
        "cost",
        "expensive",
        "cheap",
        "worth",
        "value",
        "free",
        "价格",
        "性价比",
        "值",
        "贵",
    ],
    "server": [
        "server",
        "online",
        "multiplayer",
        "connection",
        "latency",
        "ping",
        "服务器",
        "网络",
        "延迟",
        "联机",
    ],
    "community": [
        "community",
        "player",
        "toxic",
        "hacker",
        "cheater",
        "玩家",
        "社区",
        "外挂",
        "脚本",
    ],
    "content": [
        "content",
        "update",
        "dlc",
        "map",
        "mode",
        "quantity",
        "content",
        "内容",
        "更新",
        "dlc",
        "模式",
    ],
    "support": [
        "support",
        "customer",
        "response",
        "developer",
        "客服",
        "开发商",
        "售后",
        "响应",
    ],
}


class MultiLanguageSentimentAnalyzer:
    def __init__(self):
        self.models = {}
        self.tokenizer = None
        self._model_cache = {}

    def _get_lang_code(self, lang: str) -> str:
        lang_map = {
            "zh-cn": "zh",
            "zh-tw": "zh",
            "zh": "zh",
            "ja": "ja",
            "jp": "ja",
            "ko": "ko",
            "kr": "ko",
            "es": "es",
            "fr": "de",
            "de": "de",
            "ru": "ru",
            "pt": "pt",
            "it": "it",
            "en": "en",
        }
        return lang_map.get(lang.lower()[:5], "en")

    def _get_model_name(self, lang: str = "en", task: str = "sentiment") -> str:
        models = {
            ("en", "sentiment"): "cardiffnlp/twitter-roberta-base-sentiment-latest",
            ("zh", "sentiment"): "uer/roberta-base-finetuned-chinanews-chinese",
            ("ja", "sentiment"): "daigo/bert-base-japanese-sentiment",
            ("ko", "sentiment"): "beomi/kcbert-base",
            ("en", "emotion"): "bhadresh-savani/bert-base-uncased-emotion",
            ("en", "sarcasm"): "hwang/roberta-base-sarcasm",
            ("en", "toxicity"): "martin-ha/toxic-comment-model",
        }
        key = (self._get_lang_code(lang), task)
        if key not in models:
            key = ("en", task)
        return models.get(key, "cardiffnlp/twitter-roberta-base-sentiment-latest")

    def load_model(
        self, lang: str = "en", task: str = "sentiment", force: bool = False
    ):
        if not TRANSFORMERS_AVAILABLE:
            return None

        cache_key = f"{lang}_{task}"
        if cache_key in self._model_cache and not force:
            return self._model_cache[cache_key]

        try:
            model_name = self._get_model_name(lang, task)
            logger.info(f"Loading model: {model_name} for {task}")

            if task == "emotion" and lang == "en":
                classifier = pipeline(
                    "text-classification",
                    model=model_name,
                    top_k=None,
                    device=-1,
                )
            else:
                classifier = pipeline(
                    "sentiment-analysis",
                    model=model_name,
                    device=-1,
                    truncation=True,
                    max_length=512,
                )

            self._model_cache[cache_key] = classifier
            return classifier

        except Exception as e:
            logger.error(f"Failed to load model {task} for {lang}: {e}")
            return None

    def analyze_sentiment(self, text: str, lang: str = "en") -> dict:
        text = str(text)[:512]
        classifier = self.load_model(lang, "sentiment")

        if not classifier:
            return self._fallback_sentiment(text)

        try:
            result = classifier(text)[0]
            label = (
                result["label"].lower()
                if isinstance(result, dict)
                else result[0]["label"].lower()
            )
            score = result["score"] if isinstance(result, dict) else result[0]["score"]

            return {
                "label": label,
                "score": score,
                "compound": score
                if label == "positive"
                else (-score if label == "negative" else 0.0),
            }
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return self._fallback_sentiment(text)

    def analyze_emotion(self, text: str) -> dict:
        if not TRANSFORMERS_AVAILABLE:
            return {"emotion": "neutral", "score": 0.0}

        classifier = self.load_model("en", "emotion")
        if not classifier:
            return {"emotion": "neutral", "score": 0.0}

        try:
            text = str(text)[:512]
            result = classifier(text)[0]
            top_emotion = max(result, key=lambda x: x["score"])
            return {
                "emotion": top_emotion["label"].lower(),
                "score": top_emotion["score"],
                "all_scores": {r["label"]: r["score"] for r in result},
            }
        except Exception as e:
            logger.warning(f"Emotion analysis failed: {e}")
            return {"emotion": "neutral", "score": 0.0}

    def detect_sarcasm(self, text: str) -> dict:
        if not TRANSFORMERS_AVAILABLE:
            return {"is_sarcasm": False, "score": 0.0}

        classifier = self.load_model("en", "sarcasm")
        if not classifier:
            return {"is_sarcasm": False, "score": 0.0}

        try:
            text = str(text)[:512]
            result = classifier(text)[0]
            sarcasm_label = (
                result["label"].lower()
                if isinstance(result, dict)
                else result[0]["label"].lower()
            )
            score = result["score"] if isinstance(result, dict) else result[0]["score"]

            is_sarcasm = sarcasm_label == "sarcasm" or sarcasm_label == "1"
            return {
                "is_sarcasm": is_sarcasm,
                "score": score if is_sarcasm else 1 - score,
            }
        except Exception as e:
            logger.warning(f"Sarcasm detection failed: {e}")
            return {"is_sarcasm": False, "score": 0.0}

    def detect_toxicity(self, text: str) -> dict:
        if not TRANSFORMERS_AVAILABLE:
            return {"is_toxic": False, "score": 0.0}

        classifier = self.load_model("en", "toxicity")
        if not classifier:
            return {"is_toxic": False, "score": 0.0}

        try:
            text = str(text)[:512]
            result = classifier(text)[0]
            if isinstance(result, dict):
                label = result["label"].lower()
                score = result["score"]
            else:
                label = result[0]["label"].lower()
                score = result[0]["score"]

            is_toxic = label == "toxic" or label == "1"
            return {
                "is_toxic": is_toxic,
                "score": score if is_toxic else 1 - score,
            }
        except Exception as e:
            logger.warning(f"Toxicity detection failed: {e}")
            return {"is_toxic": False, "score": 0.0}

    def analyze_aspects(self, text: str) -> dict:
        text_lower = str(text).lower()
        text_lang = self._detect_lang_quick(text)

        aspect_results = {}
        for aspect, keywords in ASPECT_KEYWORDS.items():
            matched_keywords = [kw for kw in keywords if kw in text_lower]
            if matched_keywords:
                aspect_text = self._extract_sentence_with_keywords(
                    text, matched_keywords
                )
                sentiment = self.analyze_sentiment(aspect_text, text_lang)
                aspect_results[aspect] = {
                    "mentioned": True,
                    "keywords": matched_keywords,
                    "sentiment": sentiment["label"],
                    "score": sentiment["compound"],
                }
            else:
                aspect_results[aspect] = {"mentioned": False}

        return aspect_results

    def _detect_lang_quick(self, text: str) -> str:
        text = str(text)
        if any("\u4e00" <= c <= "\u9fff" for c in text):
            return "zh"
        if any("\u3040" <= c <= "\u309f" or "\u30a0" <= c <= "\u30ff" for c in text):
            return "ja"
        if any("\uac00" <= c <= "\ud7af" for c in text):
            return "ko"
        return "en"

    def _extract_sentence_with_keywords(self, text: str, keywords: list) -> str:
        text = str(text)
        for kw in keywords:
            idx = text.lower().find(kw)
            if idx != -1:
                start = max(0, idx - 50)
                end = min(len(text), idx + len(kw) + 50)
                return text[start:end]
        return text[:200]

    def _fallback_sentiment(self, text: str) -> dict:
        positive_words = {
            "good",
            "great",
            "excellent",
            "amazing",
            "love",
            "best",
            "awesome",
            "fantastic",
            "perfect",
            "fun",
            "好",
            "棒",
            "赞",
            "喜欢",
            "优秀",
        }
        negative_words = {
            "bad",
            "terrible",
            "awful",
            "worst",
            "hate",
            "boring",
            "bug",
            "crash",
            "lag",
            "垃圾",
            "差",
            "烂",
            "无聊",
            "bug",
        }

        text_lower = str(text).lower()
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)

        if pos_count > neg_count:
            return {"label": "positive", "score": 0.7, "compound": 0.7}
        elif neg_count > pos_count:
            return {"label": "negative", "score": 0.7, "compound": -0.7}
        return {"label": "neutral", "score": 0.5, "compound": 0.0}

    def analyze_complete(self, text: str, lang: str = "en") -> dict:
        sentiment = self.analyze_sentiment(text, lang)
        emotion = (
            self.analyze_emotion(text)
            if lang == "en"
            else {"emotion": "unknown", "score": 0.0}
        )
        sarcasm = self.detect_sarcasm(text)
        toxicity = self.detect_toxicity(text)
        aspects = self.analyze_aspects(text)

        return {
            "sentiment": sentiment,
            "emotion": emotion,
            "sarcasm": sarcasm,
            "toxicity": toxicity,
            "aspects": aspects,
        }


_analyzer_instance = None


def get_analyzer() -> MultiLanguageSentimentAnalyzer:
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = MultiLanguageSentimentAnalyzer()
    return _analyzer_instance


def analyze_sentiment_complete(
    df: pd.DataFrame,
    text_column: str = "review",
    lang_column: str = "detected_language",
) -> pd.DataFrame:
    df = df.copy()
    analyzer = get_analyzer()

    texts = df[text_column].fillna("").tolist()
    langs = (
        df[lang_column].fillna("en").tolist()
        if lang_column in df.columns
        else ["en"] * len(texts)
    )

    sentiments = []
    emotions = []
    sarcasms = []
    toxicities = []
    aspect_list = []

    total = len(texts)
    for i, (text, lang) in enumerate(zip(texts, langs)):
        if i % 100 == 0:
            logger.info(f"Processing {i}/{total}")

        result = analyzer.analyze_complete(text, lang)

        sentiments.append(result["sentiment"])
        emotions.append(result["emotion"])
        sarcasms.append(result["sarcasm"])
        toxicities.append(result["toxicity"])
        aspect_list.append(result["aspects"])

    df["sentiment_label"] = [s["label"] for s in sentiments]
    df["sentiment_score"] = [s["compound"] for s in sentiments]
    df["sentiment_confidence"] = [s["score"] for s in sentiments]

    df["emotion_type"] = [e["emotion"] for e in emotions]
    df["emotion_score"] = [e["score"] for e in emotions]

    df["is_sarcasm"] = [sa["is_sarcasm"] for sa in sarcasms]
    df["sarcasm_score"] = [sa["score"] for sa in sarcasms]

    df["is_toxic"] = [t["is_toxic"] for t in toxicities]
    df["toxicity_score"] = [t["score"] for t in toxicities]

    df["aspect_sentiments"] = aspect_list

    for aspect in ASPECT_KEYWORDS.keys():
        df[f"aspect_{aspect}_sentiment"] = [
            a.get(aspect, {}).get("sentiment", "none")
            if isinstance(a, dict)
            else "none"
            for a in aspect_list
        ]
        df[f"aspect_{aspect}_score"] = [
            a.get(aspect, {}).get("score", 0.0) if isinstance(a, dict) else 0.0
            for a in aspect_list
        ]

    df = df.drop(columns=["aspect_sentiments"], errors="ignore")

    logger.info("Complete sentiment analysis finished")
    logger.info(
        f"Sentiment distribution: {df['sentiment_label'].value_counts().to_dict()}"
    )
    logger.info(f"Emotion distribution: {df['emotion_type'].value_counts().to_dict()}")

    return df
