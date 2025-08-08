import pandas as pd
import logging
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
import os
import utils

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Path to the custom font file (needed for wordcloud)
font_path = os.path.join(os.path.dirname(__file__), 'wqy-MicroHei.ttf')

# Note: Font loading and NLTK downloads are handled in utils.py now

def analyze_keywords(df):
    logging.info("\n--- Performing Keyword Analysis ---")

    # Overall Keyword Analysis
    all_positive_ngrams = []
    all_negative_ngrams = []

    for index, row in df.iterrows():
        review_text = row['review']
        is_positive = row['voted_up']
        detected_lang = row['detected_language']

        if pd.isna(review_text) or not str(review_text).strip():
            continue

        processed_tokens = utils.preprocess_text(review_text, lang=detected_lang)
        processed_ngrams = utils.get_ngrams(processed_tokens, n_range=(1, 3))

        if is_positive:
            all_positive_ngrams.extend(processed_ngrams)
        else:
            all_negative_ngrams.extend(processed_ngrams)

    overall_positive_word_freq = Counter(all_positive_ngrams)
    utils.plot_word_frequencies(overall_positive_word_freq, 'Overall Positive Keywords', 'overall_positive_keywords.png')
    utils.generate_word_cloud(" ".join(all_positive_ngrams), 'Overall Positive Word Cloud', 'overall_positive_wordcloud.png', font_path)

    overall_negative_word_freq = Counter(all_negative_ngrams)
    utils.plot_word_frequencies(overall_negative_word_freq, 'Overall Negative Keywords', 'overall_negative_keywords.png')
    utils.generate_word_cloud(" ".join(all_negative_ngrams), 'Overall Negative Word Cloud', 'overall_negative_wordcloud.png', font_path)

    # Language-specific Keyword Analysis
    unique_languages = df['language'].unique()
    for lang in unique_languages:
        logging.info(f"\n--- Analyzing keywords for language: {lang} ---")
        lang_df = df[df['language'] == lang]

        if lang_df.empty:
            logging.warning(f"No reviews for language {lang}. Skipping keyword analysis.")
            continue

        # Analyze positive reviews for this language
        positive_reviews_text = " ".join(lang_df[lang_df['voted_up'] == True]['review'].dropna().tolist())
        if not positive_reviews_text.strip():
            logging.warning(f"No positive reviews text for language {lang}. Skipping positive keyword analysis.")
        else:
            cleaned_text = utils.preprocess_text(positive_reviews_text, lang=lang)
            positive_tokens = utils.preprocess_text(positive_reviews_text, lang=lang) # Use preprocess_text for tokenization
            positive_ngrams = utils.get_ngrams(positive_tokens, n_range=(1, 3))
            positive_word_freq = Counter(positive_ngrams)
            utils.plot_word_frequencies(positive_word_freq, f'{lang} 好评关键词', f'positive_keywords_{lang}.png')

        # Analyze negative reviews for this language
        negative_reviews_text = " ".join(lang_df[lang_df['voted_up'] == False]['review'].dropna().tolist())
        if not negative_reviews_text.strip():
            logging.warning(f"No negative reviews text for language {lang}. Skipping negative keyword analysis.")
        else:
            cleaned_text = utils.preprocess_text(negative_reviews_text, lang=lang)
            negative_tokens = utils.preprocess_text(negative_reviews_text, lang=lang) # Use preprocess_text for tokenization
            negative_ngrams = utils.get_ngrams(negative_tokens, n_range=(1, 3))
        negative_word_freq = Counter(negative_ngrams)
        utils.plot_word_frequencies(negative_word_freq, f'{lang} 差评关键词', f'negative_keywords_{lang}.png')
        utils.generate_word_cloud(" ".join(negative_ngrams), f'{lang} 差评词云', f'negative_wordcloud_{lang}.png', font_path)

if __name__ == "__main__":
    pass
