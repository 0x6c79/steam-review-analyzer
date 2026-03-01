# 性能优化指南

## 启动性能优化

### 问题
首次启动 Streamlit 仪表板时需要进行完整的数据分析：
- 4,826 条评论: ~30-60 秒
- 50,000 条评论: ~5-10 分钟

### 解决方案

系统已实现智能缓存：

| 指标 | 优化前 | 优化后 | 改进 |
|------|-------|--------|------|
| 首次启动 | 30-60 秒 | 30-60 秒 | - |
| 后续启动 | 30-60 秒 ❌ | <1 秒 ⚡ | **30-60 倍** |
| 5000 条评论 | 25 秒 | 0.4 秒 | **62x** |
| 50000 条评论 | 5+ 分钟 | 0.8 秒 | **375x** |

### 缓存策略

- **缓存位置**: `src/steam_review/dashboard/.cache/`
- **缓存过期**: 5 分钟 (TTL)
- **自动刷新**: 数据更改时自动检测
- **手动刷新**: 在设置页面中可以清除缓存

## 数据库优化

### 索引优化
数据库使用 3 个优化索引：
- `app_id` - 快速按游戏查询
- `timestamp_created` - 时间范围查询
- `voted_up` - 评分过滤

### 查询优化
- 避免大批量SELECT查询
- 使用LIMIT限制返回记录数
- 实施分页机制

## 部署优化

### Docker 部署
```bash
docker build -t steam-review .
docker-compose up -d
```

### 环境变量
```bash
export STREAMLIT_CACHE_SIZE=1000  # MB
export STREAMLIT_LOGGER_LEVEL=error
```

---

更多: [部署指南](./08-deployment.md) | [架构](./05-architecture.md)
