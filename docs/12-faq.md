# 常见问题 (FAQ)

## 安装和设置相关

### Q: 如何安装项目？

A: 按以下步骤操作：

```bash
# 克隆仓库
git clone https://github.com/0x6c79/steam-review-analyzer.git

# 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

详见 [快速开始指南](./01-getting-started.md)

### Q: 为什么 Python 版本必须是 3.12+？

A: 项目使用了 Python 3.12 的新特性，包括改进的类型注解和性能优化。您可以修改 `pyproject.toml` 来支持较低版本，但不保证兼容性。

### Q: 如何在 Windows 上安装？

A: 安装步骤基本相同，只是激活虚拟环境的命令不同：

```bash
# Windows 虚拟环境激活
.venv\Scripts\activate

# 其余命令相同
pip install -r requirements.txt
```

### Q: 安装依赖时出现错误怎么办？

A: 尝试以下方法：
1. 升级 pip: `pip install --upgrade pip`
2. 清除缓存: `pip cache purge`
3. 逐个安装依赖: `pip install pandas scikit-learn` 等
4. 检查 Python 版本: `python --version`

## 数据爬取相关

### Q: 爬虫速度很慢，怎样加快？

A: 这是正常的。Steam 有速率限制。您可以：

1. **耐心等待** - 这是最安全的方法
2. **并行爬取** - 不同的游戏可以并行爬取
3. **增量更新** - 使用 `--incremental` 标志只爬取新评论

```bash
# 增量爬取（只获取新评论）
python -m steam_review.scraper.steam_review_scraper --app_id 2277560 --incremental
```

### Q: 爬虫被限制了怎么办？

A: Steam API 有速率限制。如果遇到限制：

1. **等待**: 通常 30 分钟后限制解除
2. **减少并发**: 检查配置文件中的 `max_concurrent_requests`
3. **增加延迟**: 在代码中添加延迟

### Q: 可以爬取多少条评论？

A: Steam API 的限制：
- 单个游戏: 最多 20,000 条最近评论
- 更多评论需要 Steam API 权限（需要联系 Valve）

### Q: 爬虫中断了怎么办？

A: 使用增量爬取恢复：

```bash
# 这将从中断的地方继续
python -m steam_review.scraper.steam_review_scraper --app_id 2277560 --incremental
```

## 数据分析相关

### Q: 分析为什么需要这么久？

A: 分析时间取决于：
- **评论数量**: 更多数据需要更多时间
- **计算任务**: 情感分析、主题建模等都需要时间
- **计算资源**: CPU 核心数、内存等

优化方法：
- 使用缓存（仪表板自动启用）
- 减少评论数量进行测试
- 升级硬件

### Q: 首次启动仪表板需要 30-60 秒，这是正常的吗？

A: 是的，这是正常的。首次启动需要：
1. 加载数据库
2. 分析所有评论
3. 生成图表

后续访问会从缓存读取，只需 <1 秒。

### Q: 缓存多久过期？

A: 缓存默认 TTL 为 5 分钟。即：
- 新数据在 5 分钟内可能不会显示
- 您可以在设置页面手动清除缓存
- 如果源数据更改，会自动刷新

### Q: 如何强制重新分析数据？

A: 在仪表板的"设置"页面，点击"清除缓存"按钮。

## 仪表板相关

### Q: 仪表板无法访问怎么办？

A: 检查以下几点：

```bash
# 1. 确认服务正在运行
ps aux | grep streamlit

# 2. 检查端口是否被占用
lsof -i :8501

# 3. 尝试访问本地地址
curl http://localhost:8501

# 4. 查看日志
# 仪表板会在终端打印日志
```

### Q: 仪表板为什么显示"No data"？

A: 您需要先爬取评论数据：

```bash
python -m steam_review.scraper.steam_review_scraper --app_id 2277560
```

爬取完成后刷新仪表板。

### Q: 如何更改仪表板的样式？

A: 在仪表板"设置"页面修改显示选项，或编辑配置文件。

### Q: 能否在远程服务器上运行仪表板？

A: 可以。使用以下命令：

```bash
streamlit run src/steam_review/dashboard/dashboard.py \
  --server.address 0.0.0.0 \
  --server.port 8501
```

然后访问 `http://your-server-ip:8501`

## API 相关

### Q: 如何启动 API 服务？

A: 运行以下命令：

```bash
python -m steam_review.api.api
```

API 将在 http://localhost:8000 启动。

查看完整 API 文档: http://localhost:8000/docs

### Q: API 需要认证吗？

A: 当前版本不需要认证。所有端点都是公开的。

（未来版本可能会添加 API 密钥认证）

### Q: 如何从 API 导出大量数据？

A: 使用分页：

```python
import requests

BASE_URL = "http://localhost:8000"

all_reviews = []
limit = 1000
offset = 0

while True:
    response = requests.get(
        f"{BASE_URL}/reviews",
        params={
            "app_id": "2277560",
            "limit": limit,
            "offset": offset
        }
    )
    data = response.json()
    all_reviews.extend(data['reviews'])
    
    if len(data['reviews']) < limit:
        break
    
    offset += limit
```

## 数据和文件相关

### Q: 数据存储在哪里？

A: 数据存储在两个位置：

1. **CSV 文件**: `data/Game_Name_APPID_reviews.csv`
2. **SQLite 数据库**: `data/reviews.db`

### Q: 可以安全地删除缓存文件吗？

A: 可以。缓存文件在 `src/steam_review/dashboard/.cache/` 中。

删除缓存会导致：
- 下次访问仪表板时重新分析（需要时间）
- 不会丢失任何数据

### Q: 如何备份数据？

A: 简单地复制 `data/` 目录：

```bash
cp -r data/ data_backup/
```

或导出为 CSV/JSON：

```bash
# 通过仪表板导出，或使用 API
curl "http://localhost:8000/export/csv" > backup.csv
```

### Q: 数据库坏了怎么办？

A: 如果数据库损坏，您可以：

1. **删除数据库并重新爬取**:
   ```bash
   rm data/reviews.db
   python -m steam_review.scraper.steam_review_scraper --app_id 2277560
   ```

2. **从 CSV 重建**:
   ```bash
   python -c "from steam_review.storage.database import ReviewDatabase; db = ReviewDatabase(); db.import_from_csv('data/*_reviews.csv')"
   ```

## 性能和资源相关

### Q: 系统需要多少资源？

A: 最低要求：
- **CPU**: 2+ 核心
- **内存**: 2GB+ RAM
- **磁盘**: 取决于数据量（每条评论 ~2KB）

推荐配置：
- **CPU**: 4+ 核心
- **内存**: 4GB+ RAM
- **磁盘**: 10GB+（如果存储 50,000+ 条评论）

### Q: 支持多少条评论？

A: 理论上无限制，但实际考虑：
- **性能**: 100,000 条评论仍可正常工作
- **内存**: 超过 1 百万条需要增加内存
- **存储**: 100 万条 ≈ 2GB 磁盘

## 故障排除和调试

### Q: 如何查看详细日志？

A: 启用调试模式：

```bash
# Streamlit
streamlit run src/steam_review/dashboard/dashboard.py --logger.level=debug

# API
python -m steam_review.api.api --log-level debug
```

### Q: 如何报告 Bug？

A: 在 GitHub 提交 Issue：

1. 访问 https://github.com/0x6c79/steam-review-analyzer/issues
2. 点击 "New Issue"
3. 提供详细信息：
   - 错误信息
   - 复现步骤
   - 系统信息（OS、Python 版本等）

### Q: 如何要求新功能？

A: 同样在 GitHub Issues 中提交，但选择"Feature Request"标签。

## 其他问题

### Q: 项目是否支持中文？

A: 完全支持中文！

- 评论自动检测中文
- 支持中文分词（jieba）
- 中文关键词提取
- 中文词云生成

### Q: 项目如何使用？可以用于商业用途吗？

A: 项目采用 MIT 许可证，可以自由使用、修改和商业用途。

只需保留原始许可证文本即可。

### Q: 如何贡献代码？

A: 查看 [贡献指南](./10-contributing.md)

---

**仍有问题？** 

- 📧 开 Issue: https://github.com/0x6c79/steam-review-analyzer/issues
- 💬 讨论: https://github.com/0x6c79/steam-review-analyzer/discussions
- 📖 查看文档: [docs/README.md](./README.md)
