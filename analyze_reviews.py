import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
from collections import Counter
import jieba
import matplotlib.pyplot as plt
import seaborn as sns
import os
import asyncio
import matplotlib.font_manager as fm
import logging
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Ensure reproducibility for langdetect
DetectorFactory.seed = 0

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Path to the custom font file
font_path = os.path.join(os.path.dirname(__file__), 'wqy-MicroHei.ttf')

# Add the font to matplotlib's font manager
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    # Get the font name as registered by matplotlib
    prop = fm.FontProperties(fname=font_path)
    font_name = prop.get_name()

    # Set the font to be used by default
    plt.rcParams['font.family'] = font_name
    plt.rcParams['font.sans-serif'] = [font_name] # Also add to sans-serif list
    plt.rcParams['axes.unicode_minus'] = False  # Solve the problem of negative sign '-' displayed as a square
    logging.info(f"Attempting to use custom font: {font_name}")

else:
    logging.warning(f"Font file not found at {font_path}. Chinese characters might not display correctly.")
    # Fallback to other common sans-serif fonts if custom font is not found
    plt.rcParams['font.sans-serif'] = ['Source Han Sans SC', 'WenQuanYi Micro Hei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

# Download NLTK stopwords (if not already downloaded)
try:
    nltk.data.find('corpora/stopwords')
except nltk.downloader.DownloadError:
    nltk.download('stopwords')

# Function to load Chinese stopwords
def load_chinese_stopwords(file_path='chinese_stopwords.txt'):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        logging.warning(f"Chinese stopwords file not found at {file_path}. Creating a dummy one.")
        # Create a dummy Chinese stopwords file if it doesn't exist
        # In a real scenario, you would download a comprehensive list
        dummy_stopwords = "的\n了\n是\n我\n你\n他\n这\n那\n个\n不\n没有\n很\n有\n也\n都\n和\n在\n就\n一个\n什么\n自己\n"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(dummy_stopwords)
        return set(dummy_stopwords.splitlines())

chinese_stopwords = load_chinese_stopwords()
english_stopwords = set(stopwords.words('english'))

def preprocess_text(text, lang='english'):
    text = str(text).lower() # Convert to lowercase and ensure string
    text = re.sub(r'[\W_]+', ' ', text) # Remove punctuation and numbers
    if lang == 'english':
        tokens = word_tokenize(text)
        filtered_tokens = [word for word in tokens if word not in english_stopwords and len(word) > 1]
    elif lang == 'chinese':
        tokens = jieba.cut(text) # Use jieba for Chinese tokenization
        filtered_tokens = [word for word in tokens if word not in chinese_stopwords and len(word) > 1]
    else:
        filtered_tokens = []
    return filtered_tokens

def plot_sentiment_distribution(positive_count, negative_count, total_reviews):
    labels = ['好评', '差评']
    sizes = [positive_count, negative_count]
    colors = ['#66b3ff', '#ff9999']
    explode = (0.1, 0)  # explode 1st slice

    plt.figure(figsize=(8, 8))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title('评论情感分布')
    plt.savefig('sentiment_distribution.png')
    plt.close()
    logging.info("Generated sentiment_distribution.png")

def plot_word_frequencies(word_freq, title, filename):
    if not word_freq: # Check if word_freq is empty
        logging.warning(f"No data to plot for {title}. Skipping generation of {filename}.")
        return
    df_word_freq = pd.DataFrame(word_freq.most_common(20), columns=['词语', '频率'])
    plt.figure(figsize=(10, 8))
    sns.barplot(x='频率', y='词语', data=df_word_freq, palette='viridis')
    plt.title(title)
    plt.xlabel('频率')
    plt.ylabel('词语')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    logging.info(f"Generated {filename}")

def analyze_by_language(df):
    if df.empty: logging.warning("No data for language analysis. Skipping."); return
    lang_sentiment = df.groupby('language')['voted_up'].value_counts(normalize=True).unstack().fillna(0)
    lang_sentiment.columns = ['Negative', 'Positive']
    lang_sentiment = lang_sentiment.sort_values(by='Positive', ascending=False)

    plt.figure(figsize=(12, 8))
    lang_sentiment.plot(kind='bar', stacked=True, color=['#ff9999', '#66b3ff'])
    plt.title('按语言划分的评论情感分布')
    plt.xlabel('语言')
    plt.ylabel('比例')
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='情感', labels=['差评', '好评'])
    plt.tight_layout()
    plt.savefig('sentiment_by_language.png')
    plt.close()
    logging.info("Generated sentiment_by_language.png")

def analyze_by_purchase_type(df):
    if df.empty: logging.warning("No data for purchase type analysis. Skipping."); return
    purchase_sentiment = df.groupby('steam_purchase')['voted_up'].value_counts(normalize=True).unstack().fillna(0)
    purchase_sentiment.columns = ['Negative', 'Positive']
    purchase_sentiment = purchase_sentiment.sort_values(by='Positive', ascending=False)

    plt.figure(figsize=(8, 6))
    purchase_sentiment.plot(kind='bar', stacked=True, color=['#ff9999', '#66b3ff'])
    plt.title('按购买类型划分的评论情感分布')
    plt.xlabel('是否通过Steam购买')
    plt.ylabel('比例')
    plt.xticks(ticks=[0, 1], labels=['否', '是'], rotation=0)
    plt.legend(title='情感', labels=['差评', '好评'])
    plt.tight_layout()
    plt.savefig('sentiment_by_purchase_type.png')
    plt.close()
    logging.info("Generated sentiment_by_purchase_type.png")

def analyze_by_playtime(df):
    # Convert playtime to hours and handle potential non-numeric values
    df['playtime_hours'] = pd.to_numeric(df['author.playtime_forever'], errors='coerce') / 60
    df.dropna(subset=['playtime_hours', 'voted_up'], inplace=True)
    if df.empty: logging.warning("No data for playtime analysis after dropping NaNs. Skipping."); return

    # Define playtime bins and labels
    bins = [0, 1, 5, 10, 20, 50, 100, 200, 500]
    labels = ['<1h', '1-5h', '5-10h', '10-20h', '20-50h', '50-100h', '100-200h', '200-500h']

    max_playtime = df['playtime_hours'].max()
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
    plt.title('按游玩时长划分的评论情感分布')
    plt.xlabel('游玩时长 (小时)')
    plt.ylabel('比例')
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='情感', labels=['差评', '好评'])
    plt.tight_layout()
    plt.savefig('sentiment_by_playtime.png')
    plt.close()
    logging.info("Generated sentiment_by_playtime.png")

def analyze_by_early_access(df):
    if df.empty: logging.warning("No data for early access analysis. Skipping."); return
    ea_sentiment = df.groupby('written_during_early_access')['voted_up'].value_counts(normalize=True).unstack().fillna(0)
    ea_sentiment.columns = ['Negative', 'Positive']
    ea_sentiment = ea_sentiment.sort_values(by='Positive', ascending=False)

    plt.figure(figsize=(8, 6))
    ea_sentiment.plot(kind='bar', stacked=True, color=['#ff9999', '#66b3ff'])
    plt.title('早期测试阶段评论情感分布')
    plt.xlabel('是否为早期测试评论')
    plt.ylabel('比例')
    plt.xticks(ticks=[0, 1], labels=['否', '是'], rotation=0)
    plt.legend(title='情感', labels=['差评', '好评'])
    plt.tight_layout()
    plt.savefig('sentiment_by_early_access.png')
    plt.close()
    logging.info("Generated sentiment_by_early_access.png")

def analyze_by_review_length(df):
    df['review_length'] = df['review'].astype(str).apply(len)
    df.dropna(subset=['review_length', 'voted_up'], inplace=True)
    if df.empty: logging.warning("No data for review length analysis after dropping NaNs. Skipping."); return

    # Define review length bins
    bins = [0, 50, 100, 200, 500, 1000, df['review_length'].max() + 1]
    labels = ['<50', '50-100', '100-200', '200-500', '500-1000', '>1000']
    df['review_length_bin'] = pd.cut(df['review_length'], bins=bins, labels=labels, right=False)

    length_sentiment = df.groupby('review_length_bin')['voted_up'].value_counts(normalize=True).unstack().fillna(0)
    length_sentiment.columns = ['Negative', 'Positive']

    plt.figure(figsize=(12, 8))
    length_sentiment.plot(kind='bar', stacked=True, color=['#ff9999', '#66b3ff'])
    plt.title('按评论长度划分的评论情感分布')
    plt.xlabel('评论长度 (字符数)')
    plt.ylabel('比例')
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='情感', labels=['差评', '好评'])
    plt.tight_layout()
    plt.savefig('sentiment_by_review_length.png')
    plt.close()
    logging.info("Generated sentiment_by_review_length.png")

async def main_analysis():
    file_path = 'reviews.csv'
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        logging.error(f"Error: The file {file_path} was not found.")
        return

    # Add a language column to the DataFrame
    # This might take some time for large datasets
    def detect_language_robust(text):
        text = str(text).strip()
        if not text: # Handle empty strings after stripping
            return 'unknown'
        try:
            return detect(text)
        except LangDetectException:
            return 'unknown'

    df['detected_language'] = df['review'].astype(str).apply(detect_language_robust)
    df['language'] = df['detected_language'] # Use detected language for analysis

    # 1. Overall Sentiment Distribution
    total_reviews = len(df)
    positive_reviews_count = df[df['voted_up'] == True].shape[0]
    negative_reviews_count = df[df['voted_up'] == False].shape[0]

    logging.info(f"\n--- 评论情感分布 ---")
    logging.info(f"总评论数: {total_reviews}")
    logging.info(f"好评: {positive_reviews_count} ({positive_reviews_count / total_reviews:.2%})")
    logging.info(f"差评: {negative_reviews_count} ({negative_reviews_count / total_reviews:.2%})")
    plot_sentiment_distribution(positive_reviews_count, negative_reviews_count, total_reviews)

    # 2. Keyword Extraction (re-using previous logic)
    positive_reviews_text = " ".join(df[df['voted_up'] == True]['review'].dropna().tolist())
    negative_reviews_text = " ".join(df[df['voted_up'] == False]['review'].dropna().tolist())

    positive_tokens = preprocess_text(positive_reviews_text, lang='chinese') # Assuming primary language is Chinese
    negative_tokens = preprocess_text(negative_reviews_text, lang='chinese') # Assuming primary language is Chinese

    positive_word_freq = Counter(positive_tokens)
    negative_word_freq = Counter(negative_tokens)

    logging.info(f"\n--- 好评关键词 ---")
    for word, freq in positive_word_freq.most_common(20):
        logging.info(f"{word}: {freq}")
    plot_word_frequencies(positive_word_freq, '好评关键词', 'positive_keywords.png')

    logging.info(f"\n--- 差评关键词 ---")
    for word, freq in negative_word_freq.most_common(20):
        logging.info(f"{word}: {freq}")
    plot_word_frequencies(negative_word_freq, '差评关键词', 'negative_keywords.png')

    # New Analyses
    analyze_by_language(df.copy())
    analyze_by_purchase_type(df.copy())
    analyze_by_playtime(df.copy())
    analyze_by_early_access(df.copy())
    analyze_by_review_length(df.copy())

if __name__ == "__main__":
    # Ensure jieba is installed
    try:
        import jieba
    except ImportError:
        logging.warning("jieba not found. Installing jieba...")
        os.system("source .venv/bin/activate && pip install jieba")
        import jieba # Try importing again after installation

    # Download langdetect data
    try:
        detect("test")
    except Exception as e:
        logging.warning(f"langdetect data not found or error: {e}. Attempting to download.")
        # This command might require user interaction or specific permissions
        # For a robust solution, consider instructing the user to run this manually
        # or providing a more automated way if possible in your environment.
        os.system("source .venv/bin/activate && python3 -m langdetect.detector_factory --update-profile")

    asyncio.run(main_analysis())