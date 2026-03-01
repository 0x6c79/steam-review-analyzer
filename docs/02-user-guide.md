# 使用指南

完整的 Steam Review Analyzer 使用说明。

## 目录

1. [数据爬取](#数据爬取)
2. [数据分析](#数据分析)
3. [仪表板使用](#仪表板使用)
4. [数据导出](#数据导出)
5. [高级功能](#高级功能)

## 数据爬取

### 基本爬取

爬取单个游戏的所有评论：

```bash
python -m steam_review.scraper.steam_review_scraper --app_id 2277560
```

参数说明：
- `--app_id`: Steam 游戏 ID（必需）
- `--output`: 输出文件路径（可选，默认为 `data/Game_Name_APPID_reviews.csv`）
- `--timeout`: 请求超时时间（可选，默认 10 秒）
- `--max_retries`: 最大重试次数（可选，默认 5 次）

### 增量爬取

仅爬取新评论，跳过已存在的评论（节省时间和 Steam API 配额）：

```bash
python -m steam_review.scraper.steam_review_scraper --app_id 2277560 --incremental
```

### 爬取多个游戏

创建脚本爬取多个游戏：

```bash
#!/bin/bash
GAMES=(2277560 1091500 292030)  # WUCHANG, Disco Elysium, Witcher 3

for app_id in "${GAMES[@]}"; do
  python -m steam_review.scraper.steam_review_scraper --app_id $app_id
done
```

或在 Python 中：

```python
from steam_review.scraper.steam_review_scraper import SteamReviewScraper

app_ids = [2277560, 1091500, 292030]
for app_id in app_ids:
    scraper = SteamReviewScraper(app_id=app_id)
    scraper.scrape()
```

### 常见游戏 ID

| 游戏名称 | App ID |
|---------|--------|
| WUCHANG | 2277560 |
| Disco Elysium | 1091500 |
| The Witcher 3 | 292030 |
| Elden Ring | 570940 |
| Cyberpunk 2077 | 1091500 |

### 爬虫性能

- **爬取速度**: 取决于 Steam API 限制，通常 5-20 条/秒
- **网络要求**: 稳定的互联网连接
- **存储空间**: 平均每条评论约 2KB
- **时间估计**:
  - 1,000 条评论: ~1 分钟
  - 10,000 条评论: ~10 分钟
  - 100,000 条评论: ~2-3 小时

## 数据分析

### 自动分析

启动仪表板会自动对数据进行分析（推荐方式）：

```bash
streamlit run src/steam_review/dashboard/dashboard.py
```

### 命令行分析

手动分析 CSV 文件：

```bash
python -m steam_review.analysis.analyze_reviews "WUCHANG_2277560_reviews.csv"
```

### 分析包含的内容

分析会生成以下结果：

1. **情感分析**
   - 评分分布
   - 积极/消极比例
   - 时间趋势

2. **关键词提取**
   - 高频词统计
   - 词云图
   - 语言特定分析（英文、中文等）

3. **主题建模**
   - LDA 主题发现
   - 主题随时间的变化

4. **质量评分**
   - 评论质量指标
   - 有用度评估

5. **高级分析**
   - 玩家分割
   - 版本影响分析
   - 游戏基准对比

## 仪表板使用

### 启动仪表板

```bash
streamlit run src/steam_review/dashboard/dashboard.py
```

访问 http://localhost:8501

### 仪表板页面

#### 1. 概览 (Overview)
- 总体统计信息
- 评分分布
- 主要指标（正面率、平均评分等）

#### 2. 爬虫 (Scrape)
- 爬取新游戏评论
- 增量更新
- 爬虫日志和进度

#### 3. 分析 (Analysis)
- 情感分析图表
- 关键词统计
- 主题建模结果
- 时间序列分析

#### 4. 高级分析 (Advanced Analytics)
- 玩家分割
- 版本影响
- 游戏对比
- 质量评分排名

#### 5. 数据库 (Database)
- 查看和搜索所有评论
- 过滤和排序
- 数据导出

#### 6. 设置 (Settings)
- 缓存管理
- 显示选项
- 性能设置

### 缓存策略

仪表板使用智能缓存以提高性能：

- **首次分析**: 30-60 秒（取决于数据量）
- **后续访问**: <1 秒（从缓存读取）
- **自动更新**: 数据更改时自动刷新
- **手动清除**: 在设置页面中可以清除缓存

## 数据导出

### 通过仪表板导出

在仪表板的"数据库"页面点击"导出"按钮，选择格式：

- **CSV** - 纯文本，可在 Excel 中打开
- **Excel** - 格式化的工作簿
- **JSON** - 用于编程集成
- **PDF** - 用于报告

### 通过 API 导出

```bash
# 获取 API 文档
open http://localhost:8000/docs

# 导出 CSV
curl http://localhost:8000/export/csv > reviews.csv

# 导出 JSON
curl http://localhost:8000/export/json > reviews.json
```

### 通过 Python 脚本导出

```python
from steam_review.storage.database import ReviewDatabase

db = ReviewDatabase()
reviews_df = db.get_all_reviews()

# 导出为 CSV
reviews_df.to_csv('reviews.csv', index=False)

# 导出为 Excel
reviews_df.to_excel('reviews.xlsx', index=False)

# 导出为 JSON
reviews_df.to_json('reviews.json', orient='records')
```

## 高级功能

### 多语言支持

系统自动检测评论语言并进行相应的分析：

- **英文**: 完全支持
- **中文**: 完全支持（使用 jieba 分词）
- **日文**: 完全支持
- **韩文**: 完全支持
- **其他**: 40+ 种语言基本支持

### 情感分析模型

系统使用多个模型确保准确性：

1. **VADER 模型** - 快速、轻量级
2. **BERT 模型** - 深度学习、更准确

您可以在设置中选择使用的模型。

### 质量评分

评分基于多个因素：

- 评论长度
- 有用度投票
- 语言清晰度
- 详细程度

### API 集成

所有功能都可通过 RESTful API 访问：

```bash
# 启动 API 服务
python -m steam_review.api.api

# 查看完整的 API 文档
open http://localhost:8000/docs
```

## 常见任务

### 任务 1: 分析单个游戏

```bash
# 1. 爬取数据
python -m steam_review.scraper.steam_review_scraper --app_id 2277560

# 2. 启动仪表板查看结果
streamlit run src/steam_review/dashboard/dashboard.py
```

### 任务 2: 比较多个游戏

```bash
# 1. 爬取多个游戏
python -m steam_review.scraper.steam_review_scraper --app_id 2277560  # WUCHANG
python -m steam_review.scraper.steam_review_scraper --app_id 1091500  # Disco Elysium

# 2. 启动仪表板
streamlit run src/steam_review/dashboard/dashboard.py

# 3. 在高级分析标签页中选择"游戏对比"
```

### 任务 3: 导出完整报告

```bash
# 启动仪表板
streamlit run src/steam_review/dashboard/dashboard.py

# 转到数据库标签页 → 导出 → 选择 PDF 格式
```

## 故障排除

### 问题: 爬虫速度很慢

**解决**: 这是正常的。Steam 有速率限制。查看 [性能指南](./07-performance.md) 了解优化方法。

### 问题: 仪表板加载缓慢

**解决**: 
1. 检查缓存是否已启用（在设置页面）
2. 首次访问需要时间进行分析，后续访问会快得多
3. 参考 [性能指南](./07-performance.md)

### 问题: 某些评论没有被爬取

**解决**: Steam 可能隐藏了某些评论。这不是本系统的问题。

### 问题: 分析结果不准确

**解决**: 
1. 确保有足够的数据（建议 100+ 条评论）
2. 检查语言检测是否正确
3. 参考 [常见问题](./12-faq.md)

## 更多帮助

- 🔗 [系统架构](./05-architecture.md)
- 🔗 [API 参考](./03-api-reference.md)
- 🔗 [仪表板指南](./04-dashboard-guide.md)
- 🔗 [性能优化](./07-performance.md)
- 🔗 [常见问题](./12-faq.md)

---

**需要帮助？** [提交 Issue](https://github.com/0x6c79/steam-review-analyzer/issues)
