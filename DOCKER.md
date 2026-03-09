# Docker 部署指南

## 快速开始

### 构建镜像

```bash
docker build -t steam-review-analyzer .
```

### 使用 docker-compose

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| API | 8000 | FastAPI 服务 |
| Dashboard | 8501 | Streamlit 可视化界面 |
| Scraper | - | 评论爬取服务 |

## 使用 API

```bash
# 启动 API
docker-compose up api -d

# 测试 API
curl http://localhost:8000/docs
```

## 使用仪表盘

```bash
# 启动仪表盘
docker-compose up dashboard -d

# 访问 http://localhost:8501
```

## 爬取数据

```bash
# 进入容器执行爬取
docker-compose exec scraper bash
```

## 数据持久化

数据存储在 `./data` 和 `./plots` 目录中，这些目录通过 volume 挂载到容器内。

## 环境变量

可以在 `docker-compose.yml` 中添加环境变量：

```yaml
environment:
  - API_KEY=your_api_key
```
