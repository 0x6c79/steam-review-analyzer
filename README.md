# Steam Review Analyzer

Steam 游戏评论爬取与分析系统，支持数据采集、存储、可视化和高级分析。

## 🚀 快速开始

最快 5 分钟开始使用本项目：

### 方式一：本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/0x6c79/steam-review-analyzer.git
cd steam-review-analyzer

# 2. 创建虚拟环境 (需要 Python 3.12)
uv venv .venv --python python3.12
source .venv/bin/activate

# 3. 安装依赖
uv pip install -e ".[dev]"

# 4. 启动仪表盘
streamlit run src/steam_review/dashboard/dashboard.py

# 或者使用 CLI
steam-review --help
```

访问 http://localhost:8501

### 方式二：Docker 部署

```bash
# 使用 docker-compose 启动所有服务
docker-compose up -d

# 访问 API: http://localhost:8000/docs
# 访问仪表盘: http://localhost:8501
```

详细文档请参考 [DOCKER.md](./DOCKER.md)

## ✨ 功能特性

- **📊 数据爬取**: 异步爬取 Steam 评论，支持增量更新
- **💾 数据存储**: SQLite 数据库存储，支持多格式导出
- **💭 情感分析**: VADER + BERT/RoBERTa 高级模型
- **🏷️ 关键词提取**: TF-IDF 和频率分析
- **🎯 主题建模**: LDA/NMF 主题发现
- **📈 趋势预测**: 基于历史数据的评分趋势预测
- **🔔 告警机制**: 多渠道告警通知
- **🌐 Web API**: FastAPI RESTful 接口
- **📱 交互仪表盘**: Streamlit 可视化界面
- **🐳 Docker 支持**: 容器化部署
- **🌍 多语言支持**: 英文、中文、日文等 40+ 种语言

## 📚 完整文档

所有文档已组织在 [`docs/`](./docs/) 目录中：

| 文档 | 描述 |
|------|------|
| [快速开始](./docs/01-getting-started.md) | 5 分钟入门指南 |
| [使用指南](./docs/02-user-guide.md) | 详细的功能使用说明 |
| [API 参考](./docs/03-api-reference.md) | 完整的 API 文档 |
| [仪表板指南](./docs/04-dashboard-guide.md) | 仪表板功能详解 |
| [系统架构](./docs/05-architecture.md) | 系统设计和架构 |
| [数据库设计](./docs/06-database-schema.md) | 数据库和数据流 |
| [性能优化](./docs/07-performance.md) | 性能调优指南 |
| [部署指南](./docs/08-deployment.md) | Docker 和生产部署 |
| [高级分析](./docs/09-advanced-analytics.md) | 高级功能说明 |
| [贡献指南](./docs/10-contributing.md) | 如何贡献代码 |
| [路线图](./docs/11-roadmap.md) | 项目发展方向 |
| [常见问题](./docs/12-faq.md) | FAQ 和故障排除 |
| [变更日志](./docs/13-changelog.md) | 版本历史 |

## 💡 快速命令

```bash
# 交互式模式 - 选择操作
steam-review

# 爬取评论
steam-review scrape -a 2277560 -l 100

# 查看统计
steam-review stats

# 分析数据
steam-review analyze

# 启动仪表盘
steam-review dashboard
# 或
streamlit run src/steam_review/dashboard/dashboard.py

# 启动 API 服务
uvicorn src.steam_review.api.api:app --reload
```

## 📋 项目结构

```
steam-review-analyzer/
├── src/steam_review/
│   ├── __init__.py                   # 包初始化
│   ├── config.py                     # 配置
│   ├── cli/                          # CLI 命令
│   │   └── cli.py
│   ├── scraper/                      # 爬虫模块
│   │   └── steam_review_scraper.py
│   ├── analysis/                     # 分析模块
│   │   ├── analyze_reviews.py
│   │   ├── sentiment_analysis.py
│   │   └── ...
│   ├── dashboard/                    # Streamlit 仪表盘
│   │   └── dashboard.py
│   ├── storage/                      # 数据库
│   │   └── database.py
│   └── utils/                        # 工具函数
├── data/                             # 数据目录
├── plots/                            # 生成的图表
├── src/tests/                        # 测试
├── pyproject.toml                    # 项目配置
└── README.md                         # 本文件
```

## 🎯 针对不同用户

### 👤 普通用户
1. 阅读 [快速开始](./docs/01-getting-started.md)
2. 查看 [使用指南](./docs/02-user-guide.md)
3. 参考 [仪表板指南](./docs/04-dashboard-guide.md)

### 🧑‍💻 开发者
1. 阅读 [快速开始](./docs/01-getting-started.md)
2. 查看 [贡献指南](./docs/10-contributing.md)
3. 研究 [系统架构](./docs/05-architecture.md)

### 🔌 API 使用者
1. 启动 API: `python -m steam_review.api.api`
2. 访问 API 文档: http://localhost:8000/docs
3. 查看 [API 参考](./docs/03-api-reference.md)

### 🚀 DevOps 工程师
1. 查看 [部署指南](./docs/08-deployment.md)
2. 了解 [性能优化](./docs/07-performance.md)
3. 研究 [系统架构](./docs/05-architecture.md)

## 📊 主要特性对比

| 功能 | 仪表盘 | API | CLI | 说明 |
|------|--------|-----|-----|------|
| 爬取评论 | ✅ | ✅ | ✅ | 支持所有方式 |
| 数据分析 | ✅ | ✅ | ✅ | 自动分析数据 |
| 可视化 | ✅ | ❌ | ❌ | 仅在仪表盘显示 |
| 数据导出 | ✅ | ✅ | ❌ | 支持多种格式 |
| 定制性 | 📊 低 | 🔧 高 | 📝 高 | API 和 CLI 更灵活 |

## 🔧 系统要求

| 需求 | 最低 | 推荐 |
|------|------|------|
| Python | 3.12+ | 3.12+ |
| 内存 | 2GB | 4GB+ |
| 磁盘 | 1GB | 10GB+ |
| CPU | 2 核 | 4 核+ |

## 📦 主要依赖

- **数据处理**: pandas, numpy
- **机器学习**: scikit-learn, transformers
- **Web 框架**: fastapi, streamlit
- **可视化**: plotly, matplotlib, seaborn
- **数据库**: sqlite3

完整依赖见 [requirements.txt](./requirements.txt)

## 📈 性能指标

| 指标 | 值 |
|------|-----|
| 爬取速度 | 5-20 评论/秒 |
| 首次分析 | 30-60 秒（取决于数据量） |
| 后续访问 | <1 秒（使用缓存） |
| 单数据库容量 | 1-2 百万条评论 |
| 仪表盘响应 | <200ms |

## 🤝 贡献

欢迎提交 Pull Requests 和 Issues！

详见 [贡献指南](./docs/10-contributing.md)

## 📄 许可证

MIT License - 详见 [LICENSE](./LICENSE)

## 🔗 链接

- 🌐 [GitHub 仓库](https://github.com/0x6c79/steam-review-analyzer)
- 📝 [完整文档](./docs/README.md)
- 🐛 [报告问题](https://github.com/0x6c79/steam-review-analyzer/issues)
- 💬 [讨论区](https://github.com/0x6c79/steam-review-analyzer/discussions)
- ⭐ [给个 Star](https://github.com/0x6c79/steam-review-analyzer)

---

**版本**: v1.0.0 | **最后更新**: 2026-03-01
