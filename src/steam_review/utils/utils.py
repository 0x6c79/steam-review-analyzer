import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import scipy.stats as stats
import os
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import jieba
from wordcloud import WordCloud
import matplotlib.font_manager as fm
from .. import config

font_path_wqy = config.FONT_PATHS['chinese']
font_path_noto = config.FONT_PATHS['noto']

def _configure_chinese_font():
    """Ensure Chinese font is configured for matplotlib"""
    if os.path.exists(font_path_wqy):
        try:
            fm.fontManager.addfont(font_path_wqy)
        except Exception:
            pass
        if 'WenQuanYi Micro Hei' not in plt.rcParams.get('font.sans-serif', []):
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'Noto Sans'] + plt.rcParams.get('font.sans-serif', [])
    if os.path.exists(font_path_noto):
        try:
            fm.fontManager.addfont(font_path_noto)
        except Exception:
            pass
    plt.rcParams['axes.unicode_minus'] = False

_configure_chinese_font()

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['figure.figsize'] = (10, 6)

config.setup_logging()

# Ensure NLTK stopwords are downloaded
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def load_chinese_stopwords(file_path=None):
    if file_path is None:
        file_path = config.CHINESE_STOPWORDS_FILE
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        logging.warning(f"Chinese stopwords file not found at {file_path}. Using empty set.")
        return set()

chinese_stopwords = load_chinese_stopwords()

def preprocess_text(text, lang='english'):
    text = str(text).lower()
    if lang == 'english':
        tokens = word_tokenize(text)
        filtered_tokens = [word for word in tokens if word.isalpha() and word not in stopwords.words('english')]
    elif lang == 'chinese':
        tokens = jieba.cut(text, cut_all=False)
        filtered_tokens = [word for word in tokens if word.strip() and word not in chinese_stopwords]
    else:
        filtered_tokens = [word for word in word_tokenize(text) if word.isalpha()]
    return filtered_tokens

def get_ngrams(tokens, n_range=(1, 1)):
    ngrams = []
    for n in range(n_range[0], n_range[1] + 1):
        ngrams.extend([' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)])
    return ngrams

def plot_word_frequencies(word_freq, title, filename, top_n=20):
    _configure_chinese_font()
    common_words = word_freq.most_common(top_n)
    if not common_words:
        logging.warning(f"No common words to plot for {title}. Skipping.")
        return
    words, counts = zip(*common_words)

    plt.figure(figsize=(12, 7))
    df_plot = pd.DataFrame({'words': list(words), 'counts': list(counts)})
    sns.barplot(x='counts', y='words', data=df_plot, hue='words', palette='viridis', legend=False)
    plt.title(title)
    plt.xlabel('Frequency')
    plt.ylabel('Words')
    plt.tight_layout()
    plt.savefig(f'plots/{filename}')
    plt.close()
    logging.info(f"Generated plots/{filename}")

def generate_word_cloud(text, title, filename, font_path=None):
    if not text.strip():
        logging.warning(f"No text to generate word cloud for {title}. Skipping.")
        return

    wordcloud = WordCloud(width=800, height=400, background_color='white', font_path=font_path).generate(text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    if font_path and os.path.exists(font_path):
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
        plt.rcParams['axes.unicode_minus'] = False
    plt.title(title)
    plt.tight_layout()
    plt.savefig(f'plots/{filename}')
    plt.close()
    logging.info(f"Generated plots/{filename}")

def analyze_by_playtime(df, filename_base):
    _configure_chinese_font()
    # Convert playtime to hours and handle potential non-numeric values
    df['playtime_hours'] = pd.to_numeric(df['author.playtime_forever'], errors='coerce') / 60
    df.dropna(subset=['playtime_hours', 'voted_up'], inplace=True)
    if df.empty:
        logging.warning("No data for playtime analysis after dropping NaNs. Skipping.")
        return

    # Calculate Point-Biserial Correlation
    # Convert 'voted_up' to numeric (True=1, False=0) for correlation
    df['voted_up_numeric'] = df['voted_up'].astype(int)
    correlation, p_value = stats.pointbiserialr(df['playtime_hours'], df['voted_up_numeric'])
    logging.info(f"游玩时长与评论情感的点二列相关系数: {correlation:.2f} (p-value: {p_value:.3f})")

    # Define playtime bins and labels
    bins = [0, 1, 5, 10, 20, 50, 100, 200, 500]
    labels = ['<1h', '1-5h', '5-10h', '10-20h', '20-50h', '50-100h', '100-200h', '200-500h']

    max_playtime = df['playtime_hours'].max()
    if pd.isna(max_playtime): # Handle case where max_playtime is NaN (e.g., all playtime_hours were NaN)
        logging.warning("max_playtime is NaN. Skipping playtime binning.")
        return

    if max_playtime > bins[-1]:
        bins.append(max_playtime + 1) # Add a bin just above the max playtime
        labels.append(f'>={bins[-2]:.0f}h') # Add a corresponding label

    # Ensure bins are unique and sorted
    unique_bins = sorted(list(set(bins)))
    # Adjust labels to match the number of unique bins - 1
    final_labels = []
    for i in range(len(unique_bins) - 1):
        if i < len(labels):
            final_labels.append(labels[i])
        else:
            final_labels.append(f'{unique_bins[i]:.0f}-{unique_bins[i+1]:.0f}h')

    if len(final_labels) != len(unique_bins) - 1:
        logging.error(f"Mismatch in bins and labels for playtime analysis. Bins: {unique_bins}, Labels: {final_labels}")
        return

    df['playtime_bin'] = pd.cut(df['playtime_hours'], bins=unique_bins, labels=final_labels, right=False, include_lowest=True)

    playtime_sentiment = df.groupby('playtime_bin')['voted_up'].value_counts(normalize=True).unstack().fillna(0)
    playtime_sentiment.columns = ['Negative', 'Positive']

    plt.figure(figsize=(14, 8))
    playtime_sentiment.plot(kind='bar', stacked=True, color=['#ff9999', '#66b3ff'])
    plt.title(f'按游玩时长划分的评论情感分布 (评论数: {len(df)})')
    plt.xlabel('游玩时长 (小时)')
    plt.ylabel('比例')
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='情感', labels=['差评', '好评'])
    plt.tight_layout()
    plt.savefig(f'plots/{filename_base}_sentiment_by_playtime.png')
    plt.close()
    logging.info("Generated plots/sentiment_by_playtime.png")

    # Box plot for playtime vs. sentiment
    plt.figure(figsize=(12, 7))
    sns.boxplot(x='voted_up', y='playtime_hours', data=df, palette=['#ff9999', '#66b3ff'])
    plt.title(f'游玩时长与评论情感的箱线图 (评论数: {len(df)})')
    plt.xlabel('评论情感 (False: 差评, True: 好评)')
    plt.ylabel('游玩时长 (小时)')
    plt.yscale('log') # Use log scale for playtime if it has a wide range
    plt.tight_layout()
    plt.savefig(f'plots/{filename_base}_playtime_sentiment_boxplot.png')
    plt.close()
    logging.info("Generated plots/playtime_sentiment_boxplot.png")

def analyze_by_review_length(df, filename_base):
    _configure_chinese_font()
    df['review_length'] = df['review'].astype(str).apply(len)
    df.dropna(subset=['review_length', 'voted_up'], inplace=True)
    if df.empty:
        logging.warning("No data for review length analysis after dropping NaNs. Skipping.")
        return

    # Define review length bins
    bins = [0, 50, 100, 200, 500, 1000, float('inf')]
    labels = ['<50', '50-100', '100-200', '200-500', '500-1000', '>1000']
    df['review_length_bin'] = pd.cut(df['review_length'], bins=bins, labels=labels, right=False)

    length_sentiment = df.groupby('review_length_bin')['voted_up'].value_counts(normalize=True).unstack().fillna(0)
    length_sentiment.columns = ['Negative', 'Positive']

    plt.figure(figsize=(12, 8))
    length_sentiment.plot(kind='bar', stacked=True, color=['#ff9999', '#66b3ff'])
    plt.title(f'按评论长度划分的评论情感分布 (评论数: {len(df)})')
    plt.xlabel('评论长度 (字符数)')
    plt.ylabel('比例')
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='情感', labels=['差评', '好评'])
    plt.tight_layout()
    plt.savefig(f'plots/{filename_base}_sentiment_by_review_length.png')
    plt.close()
    logging.info("Generated plots/sentiment_by_review_length.png")

    # Calculate Point-Biserial Correlation
    df['voted_up_numeric'] = df['voted_up'].astype(int)
    correlation, p_value = stats.pointbiserialr(df['review_length'], df['voted_up_numeric'])
    logging.info(f"评论长度与评论情感的点二列相关系数: {correlation:.2f} (p-value: {p_value:.3f})")

    # Box plot for review length vs. sentiment
    plt.figure(figsize=(12, 7))
    sns.boxplot(x='voted_up', y='review_length', data=df, palette=['#ff9999', '#66b3ff'])
    plt.title(f'评论长度与评论情感的箱线图 (评论数: {len(df)})')
    plt.xlabel('评论情感 (False: 差评, True: 好评)')
    plt.ylabel('评论长度 (字符数)')
    plt.yscale('log') # Use log scale for review length if it has a wide range
    plt.tight_layout()
    plt.savefig(f'plots/{filename_base}_review_length_sentiment_boxplot.png')
    plt.close()
    logging.info("Generated plots/review_length_sentiment_boxplot.png")

def analyze_by_early_access(df, filename_base):
    _configure_chinese_font()
    if df.empty:
        logging.warning("No data for early access analysis. Skipping.")
        return
    ea_sentiment = df.groupby('written_during_early_access')['voted_up'].value_counts(normalize=True).unstack().fillna(0)
    ea_sentiment.columns = ['Negative', 'Positive']
    ea_sentiment = ea_sentiment.sort_values(by='Positive', ascending=False)

    plt.figure(figsize=(8, 6))
    ea_sentiment.plot(kind='bar', stacked=True, color=['#ff9999', '#66b3ff'])
    plt.title(f'早期测试阶段评论情感分布 (评论数: {len(df)})')
    plt.xlabel('是否为早期测试评论')
    plt.ylabel('比例')
    plt.xticks(ticks=[0, 1], labels=['否', '是'], rotation=0)
    plt.legend(title='情感', labels=['差评', '好评'])
    plt.tight_layout()
    plt.savefig(f'plots/{filename_base}_sentiment_by_early_access.png')
    plt.close()
    logging.info("Generated plots/sentiment_by_early_access.png")

def plot_sentiment_distribution(positive_reviews_count, negative_reviews_count, total_reviews):
    _configure_chinese_font()
    labels = ['Positive', 'Negative']
    sizes = [positive_reviews_count, negative_reviews_count]
    colors = ['#66b3ff', '#ff9999']
    explode = (0.1, 0)  # explode 1st slice

    plt.figure(figsize=(8, 8))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=140)
    plt.title(f'Overall Sentiment Distribution (Total Reviews: {total_reviews})')
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.savefig('plots/sentiment_distribution.png')
    plt.close()
    logging.info("Generated plots/sentiment_distribution.png")

def plot_sentiment_over_time(df, title, filename):
    _configure_chinese_font()
    plt.figure(figsize=(12, 6))
    plt.plot(df['time_period'], df['Positive_Ratio'], label='Positive Ratio', color='green')
    plt.plot(df['time_period'], df['Negative_Ratio'], label='Negative Ratio', color='red')
    plt.title(title)
    plt.xlabel('Time')
    plt.ylabel('Ratio')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'plots/{filename}')
    plt.close()
    logging.info(f"Generated plots/{filename}")