import sys
import os
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import logging
from collections import Counter
from src.steam_review.utils import utils
from src.steam_review import config

font_path = config.FONT_PATHS['chinese']

def analyze_keywords(df):
    logging.info("\n--- Performing Keyword Analysis ---")

    df_filtered = df.dropna(subset=['review']).copy()
    df_filtered = df_filtered[df_filtered['review'].astype(str).str.strip() != '']

    positive_text = " ".join(df_filtered[df_filtered['voted_up']]['review'].astype(str).tolist())
    negative_text = " ".join(df_filtered[~df_filtered['voted_up']]['review'].astype(str).tolist())

    positive_tokens = utils.preprocess_text(positive_text, lang='en')
    negative_tokens = utils.preprocess_text(negative_text, lang='en')

    positive_ngrams = utils.get_ngrams(positive_tokens, n_range=(1, 3))
    negative_ngrams = utils.get_ngrams(negative_tokens, n_range=(1, 3))

    overall_positive_word_freq = Counter(positive_ngrams)
    utils.plot_word_frequencies(overall_positive_word_freq, 'Overall Positive Keywords', 'overall_positive_keywords.png')
    utils.generate_word_cloud(" ".join(positive_ngrams), 'Overall Positive Word Cloud', 'overall_positive_wordcloud.png', font_path)

    overall_negative_word_freq = Counter(negative_ngrams)
    utils.plot_word_frequencies(overall_negative_word_freq, 'Overall Negative Keywords', 'overall_negative_keywords.png')
    utils.generate_word_cloud(" ".join(negative_ngrams), 'Overall Negative Word Cloud', 'overall_negative_wordcloud.png', font_path)

    # Language-specific Keyword Analysis
    unique_languages = df['detected_language'].unique()
    for lang in unique_languages:
        logging.info(f"\n--- Analyzing keywords for language: {lang} ---")
        lang_df = df[df['detected_language'] == lang]

        if lang_df.empty:
            logging.warning(f"No reviews for language {lang}. Skipping keyword analysis.")
            continue

        # Analyze positive reviews for this language
        positive_reviews_text = " ".join(lang_df[lang_df['voted_up']]['review'].dropna().tolist())
        if not positive_reviews_text.strip():
            logging.warning(f"No positive reviews text for language {lang}. Skipping positive keyword analysis.")
        else:
            
            positive_tokens = utils.preprocess_text(positive_reviews_text, lang=lang) # Use preprocess_text for tokenization
            positive_ngrams = utils.get_ngrams(positive_tokens, n_range=(1, 3))
            positive_word_freq = Counter(positive_ngrams)
            utils.plot_word_frequencies(positive_word_freq, f'{lang} 好评关键词', f'positive_keywords_{lang}.png')

        # Analyze negative reviews for this language
        negative_reviews_text = " ".join(lang_df[~lang_df['voted_up']]['review'].dropna().tolist())
        if negative_reviews_text.strip():
            negative_tokens = utils.preprocess_text(negative_reviews_text, lang=lang)
            negative_ngrams = utils.get_ngrams(negative_tokens, n_range=(1, 3))
            negative_word_freq = Counter(negative_ngrams)
            utils.plot_word_frequencies(negative_word_freq, f'{lang} 差评关键词', f'negative_keywords_{lang}.png')
            utils.generate_word_cloud(" ".join(negative_ngrams), f'{lang} 差评词云', f'negative_wordcloud_{lang}.png', font_path)
        else:
            logging.warning(f"No negative reviews text for language {lang}. Skipping negative keyword analysis.")

if __name__ == "__main__":
    pass
