# Steam Review Analyzer - 项目规范文档

## 1. 项目概述

Steam 游戏评论分析工具，支持爬取、存储、分析和可视化 Steam 游戏评论。

### 核心功能
- **爬取**: 从 Steam API 获取游戏评论
- **存储**: SQLite 数据库存储评论数据
- **分析**: 情感分析、关键词提取、时间序列分析、相关性分析
- **可视化**: Streamlit 仪表盘、Plotly 图表
- **CLI**: 用户友好的命令行界面

## 2. 技术栈

| 组件 | 技术 |
|------|------|
| Python | 3.12 |
| 数据库+ | SQLite (aiosqlite) |
| Web 框架 | FastAPI, Streamlit |
| 数据处理 | Pandas, NumPy |
| NLP | NLTK, langdetect, jieba |
| 可视化 | Plotly, Matplotlib, Seaborn, WordCloud |
| CLI | Click |
| 测试 | pytest, pytest-asyncio |

### 依赖管理
```bash
# 核心依赖
uv pip install -e ".[dev]"

# 可选 ML 依赖（需要额外磁盘空间）
uv pip install -e ".[ml]"  # transformers, torch
```

## 3. 项目结构

```
steam_review/
├── src/
│   └── steam_review/
│       ├── __init__.py          # 统一 sys.path 管理
│       ├── config.py            # 配置（游戏名、路径、参数）
│       ├── cli/                 # 命令行界面
│       │   └── cli.py           # Click CLI（推荐使用）
│       ├── scraper/              # 数据爬取
│       │   └── steam_review_scraper.py
│       ├── storage/             # 数据存储
│       │   ├── database.py      # SQLite 操作
│       │   └── async_database.py
│       ├── analysis/            # 数据分析
│       │   ├── analyze_reviews.py
│       │   ├── sentiment_analysis.py
│       │   ├── sentiment_analysis_enhanced.py  # 增强版情感分析
│       │   ├── keyword_analysis.py
│       │   ├── time_series_analysis.py
│       │   └── correlation_analysis.py
│       ├── dashboard/           # Streamlit 仪表盘
│       │   └── dashboard.py
│       ├── api/                 # FastAPI 接口
│       │   └── api.py
│       └── utils/               # 工具函数
├── data/                       # 数据目录
├── plots/                      # 生成的图表
├── config.json                 # 配置文件
└── pyproject.toml             # 项目配置
```

## 4. 关键模块说明

### 4.1 配置模块 (config.py)
- `PROJECT_ROOT`: 项目根目录
- `GAME_NAMES`: App ID 到游戏名的映射
- `SCRAPER_CONFIG`: 爬虫配置（并发数、超时、重试）
- `ANALYSIS_CONFIG`: 分析配置（游玩时间分组、评论长度分组）
- `get_game_name(app_id)`: 获取游戏名

### 4.2 爬虫模块 (scraper/)
- `get_reviews()`: 异步获取评论，支持重试和限流处理
- `get_app_details()`: 获取游戏信息
- `flatten_review()`: 展平嵌套评论数据
- `load_checkpoint()` / `save_checkpoint()`: 断点续传

### 4.3 数据库模块 (storage/)
- `insert_reviews(df)`: 批量插入评论
- `get_reviews(app_id, limit)`: 查询评论
- `get_stats(app_id)`: 获取统计数据
- `get_all_games()`: 获取所有游戏列表

### 4.4 分析模块 (analysis/)
- `sentiment_analysis_enhanced.py`: 增强情感分析（多语言、方面情感、情绪检测）
- `analyze_reviews.py`: 主分析流程（语言检测、特征工程）

### 4.5 CLI (cli/cli.py)
```bash
steam-review              # 交互模式
steam-review scrape -a 2277560 -l 100
steam-review stats
steam-review dashboard
```

## 5. 开发规范

### 5.1 导入规范
**重要**: 不要在模块中手动添加 sys.path。所有模块应该通过包名导入：

```python
# ✅ 正确
from src.steam_review.storage.database import get_database
from src.steam_review import config

# ❌ 错误（已废弃）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### 5.2 路径管理
项目使用统一的路径管理：
- `src/steam_review/__init__.py` 自动将项目根目录添加到 sys.path
- 所有模块使用相对导入

### 5.3 类型注解
- 使用 Python 3.12 类型注解
- 推荐添加函数返回类型

### 5.4 错误处理
- 使用具体的异常类型
- 添加重试逻辑（网络请求）
- 记录详细的日志

## 6. 测试规范

### 6.1 测试文件位置
```
src/tests/
├── test_database.py
├── test_config.py
├── test_cli.py
├── test_scraper.py
└── test_analyze_reviews.py
```

### 6.2 运行测试
```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行所有测试
python -m pytest src/tests/ -v

# 带覆盖率
python -m pytest src/tests/ --cov=src.steam_review --cov-report=term-missing
```

### 6.3 测试规范
- 使用 pytest fixtures
- 异步测试使用 `@pytest.mark.asyncio`
- Mock 外部依赖
- 使用临时目录 `tmp_path` 处理文件操作

### 6.4 测试覆盖率目标
| 模块 | 目标 |
|------|------|
| config | 90%+ |
| scraper | 70%+ |
| database | 50%+ |
| cli | 50%+ |

## 7. 常用命令

### 7.1 开发环境
```bash
# 创建虚拟环境
uv venv .venv --python python3.12
source .venv/bin/activate

# 安装依赖
uv pip install -e ".[dev]"

# 安装可选 ML 依赖
uv pip install -e ".[ml]"
```

### 7.2 CLI 命令
```bash
# 交互模式
steam-review

# 爬取评论
steam-review scrape -a 2277560 -l 100

# 查看统计
steam-review stats

# 启动仪表盘
steam-review dashboard

# 分析数据
steam-review analyze data/game_reviews.csv
```

### 7.3 API 服务
```bash
# 启动 FastAPI
uvicorn src.steam_review.api.api:app --reload

# 启动 Streamlit
streamlit run src/steam_review/dashboard/dashboard.py
```

## 8. 注意事项

### 8.1 Python 版本
- 项目要求 **Python 3.12+**
- 使用 uv 管理虚拟环境
- 不要在 Python 3.14 上运行（依赖兼容性问题）

### 8.2 依赖问题
- torch/transformers 作为可选依赖 `[ml]`
- 某些依赖可能需要系统库（如字体）

### 8.3 常见问题
1. **导入错误**: 确保虚拟环境已激活
2. **数据库锁定**: 使用 aiosqlite 或关闭连接
3. **Steam API 限流**: 爬虫已内置重试逻辑

## 9. 贡献指南

1. 创建功能分支
2. 添加测试用例
3. 确保所有测试通过
4. 更新文档
5. 提交 PR
