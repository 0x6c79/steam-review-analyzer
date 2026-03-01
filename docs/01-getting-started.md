# 快速开始指南

5分钟内快速上手 Steam Review Analyzer！

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/0x6c79/steam-review-analyzer.git
cd steam-review-analyzer
```

### 2. 创建虚拟环境

```bash
python3.12 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 基本使用

### 方式 1️⃣: 使用交互式仪表板（推荐）

```bash
streamlit run src/steam_review/dashboard/dashboard.py
```

然后在浏览器中打开 http://localhost:8501

### 方式 2️⃣: 使用命令行工具

**爬取评论**:
```bash
python -m steam_review.scraper.steam_review_scraper --app_id 2277560
```

**分析评论**:
```bash
python -m steam_review.analysis.analyze_reviews "WUCHANG_2277560_reviews.csv"
```

### 方式 3️⃣: 使用 API 服务

```bash
python -m steam_review.api.api
```

访问 http://localhost:8000/docs 查看 API 文档

## 常见命令

| 命令 | 说明 |
|------|------|
| `streamlit run ...` | 启动交互式仪表板 |
| `python -m steam_review.scraper.steam_review_scraper --app_id <ID>` | 爬取游戏评论 |
| `python -m steam_review.analysis.analyze_reviews <CSV_FILE>` | 分析评论数据 |
| `python -m steam_review.api.api` | 启动 API 服务 |

## 📂 重要文件和目录

```
steam-review-analyzer/
├── data/              # 爬取的数据存储位置
├── plots/             # 生成的图表
├── src/
│   └── steam_review/
│       ├── scraper/   # 爬虫模块
│       ├── analysis/  # 分析模块
│       ├── dashboard/ # 仪表板
│       └── api/       # API 服务
└── docs/              # 文档（您在这里）
```

## 👉 下一步

1. **了解功能**: 查看 [使用指南](./02-user-guide.md)
2. **深入学习**: 阅读 [仪表板指南](./04-dashboard-guide.md)
3. **理解架构**: 查看 [系统架构](./05-architecture.md)
4. **部署生产**: 参考 [部署指南](./08-deployment.md)

## ❓ 常见问题

**Q: 爬虫速度太慢？**  
A: 这是正常的，Steam 有速率限制。查看 [性能指南](./07-performance.md) 了解优化技巧。

**Q: 如何爬取多个游戏？**  
A: 参考 [使用指南](./02-user-guide.md#爬取多个游戏)

**Q: 数据存储在哪里？**  
A: 数据存储在 `data/` 目录下的 CSV 文件和 SQLite 数据库中。

**Q: 如何导出数据？**  
A: 在仪表板的"导出"页面或使用 API `/export/{format}` 端点。

## 🔗 更多资源

- [GitHub 仓库](https://github.com/0x6c79/steam-review-analyzer)
- [问题报告](https://github.com/0x6c79/steam-review-analyzer/issues)
- [讨论区](https://github.com/0x6c79/steam-review-analyzer/discussions)
- [完整文档](./README.md)

---

**遇到问题？** 查看 [常见问题](./12-faq.md) 或 [提交 Issue](https://github.com/0x6c79/steam-review-analyzer/issues)
