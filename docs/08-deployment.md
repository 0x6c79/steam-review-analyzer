# 部署指南

## 本地部署

### 要求
- Python 3.12+
- SQLite 3.0+
- 2GB 磁盘空间（用于数据库）

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/0x6c79/steam-review-analyzer.git
cd steam-review-analyzer

# 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动仪表板
streamlit run src/steam_review/dashboard/dashboard.py
```

## Docker 部署

### 构建镜像
```bash
docker build -t steam-review .
```

### 运行容器
```bash
# 前台运行
docker run -p 8501:8501 steam-review

# 后台运行
docker run -d -p 8501:8501 steam-review

# 使用数据卷
docker run -v steam-data:/app/data -p 8501:8501 steam-review
```

### Docker Compose
```bash
docker-compose up -d
```

## 生产部署

### Nginx 反向代理

```nginx
upstream streamlit {
    server localhost:8501;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Systemd 服务

```ini
[Unit]
Description=Steam Review Analyzer
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/steam-review-analyzer
ExecStart=/opt/steam-review-analyzer/.venv/bin/streamlit run src/steam_review/dashboard/dashboard.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 环境配置

### 必要的环境变量
```bash
STEAM_API_TIMEOUT=10
BATCH_SIZE=1000
LOG_LEVEL=info
```

### 可选的性能调整
```bash
STREAMLIT_CACHE_SIZE=2000  # MB
STREAMLIT_LOGGER_LEVEL=error
STREAMLIT_SERVER_MAXUPLOADSIZE=200  # MB
```

---

更多: [性能优化](./07-performance.md) | [架构](./05-architecture.md)
