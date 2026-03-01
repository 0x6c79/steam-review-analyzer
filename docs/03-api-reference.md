# API 参考文档

Steam Review Analyzer FastAPI 完整参考。

## 快速开始

### 启动 API 服务

```bash
python -m steam_review.api.api
```

API 服务将在 `http://localhost:8000` 启动。

### 访问文档

API 文档自动生成（由 FastAPI 提供）：

- **交互式文档** (Swagger UI): http://localhost:8000/docs
- **备选文档** (ReDoc): http://localhost:8000/redoc
- **OpenAPI 模式**: http://localhost:8000/openapi.json

## API 端点

### 1. 获取评论列表

```http
GET /reviews
```

**参数**:
| 参数 | 类型 | 说明 | 示例 |
|-----|------|------|------|
| `app_id` | string | 游戏 App ID | `2277560` |
| `limit` | int | 返回数量（最多 1000） | `100` |
| `offset` | int | 跳过的数量 | `0` |
| `language` | string | 过滤语言（仅 API） | `en` |
| `sentiment` | string | 过滤情感（正/负/中立） | `positive` |

**示例**:
```bash
curl "http://localhost:8000/reviews?app_id=2277560&limit=10"
```

**响应**:
```json
{
  "total": 5000,
  "reviews": [
    {
      "recommendation_id": "abc123",
      "app_id": "2277560",
      "review": "Great game!",
      "voted_up": true,
      "sentiment_score": 0.95,
      "language": "en",
      "timestamp_created": 1703001600
    }
  ]
}
```

### 2. 获取单条评论

```http
GET /reviews/{recommendation_id}
```

**示例**:
```bash
curl "http://localhost:8000/reviews/abc123"
```

**响应**:
```json
{
  "recommendation_id": "abc123",
  "app_id": "2277560",
  "review": "Great game!",
  "voted_up": true,
  "sentiment_score": 0.95,
  "language": "en",
  "timestamp_created": 1703001600,
  "playtime_forever": 50.5,
  "author_num_games_owned": 120
}
```

### 3. 获取统计数据

```http
GET /stats
```

**参数**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| `app_id` | string | 游戏 App ID（可选） |

**示例**:
```bash
curl "http://localhost:8000/stats?app_id=2277560"
```

**响应**:
```json
{
  "total_reviews": 5000,
  "positive_count": 4200,
  "negative_count": 800,
  "positive_rate": 0.84,
  "average_sentiment": 0.72,
  "average_playtime": 50.5,
  "languages": {
    "en": 2500,
    "zh-cn": 1500,
    "ja": 500,
    "other": 500
  }
}
```

### 4. 获取语言统计

```http
GET /languages
```

**参数**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| `app_id` | string | 游戏 App ID（可选） |

**示例**:
```bash
curl "http://localhost:8000/languages?app_id=2277560"
```

**响应**:
```json
{
  "en": 2500,
  "zh-cn": 1500,
  "ja": 500,
  "ko": 300,
  "other": 200
}
```

### 5. 导出数据

```http
GET /export/{format}
```

**格式支持**:
- `csv` - 逗号分隔值
- `json` - JSON 格式
- `excel` - Excel 工作簿
- `pdf` - PDF 报告

**参数**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| `app_id` | string | 游戏 App ID（可选） |
| `limit` | int | 导出数量（可选） |

**示例**:
```bash
# 导出为 CSV
curl "http://localhost:8000/export/csv?app_id=2277560" -o reviews.csv

# 导出为 JSON
curl "http://localhost:8000/export/json?limit=1000" -o reviews.json

# 导出为 Excel
curl "http://localhost:8000/export/excel" -o reviews.xlsx
```

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误信息"
}
```

### 常见错误

| HTTP 状态码 | 说明 |
|------------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

**示例错误响应**:
```json
{
  "detail": "App ID not found"
}
```

## Python 客户端示例

### 使用 requests 库

```python
import requests

BASE_URL = "http://localhost:8000"

# 获取评论
response = requests.get(
    f"{BASE_URL}/reviews",
    params={
        "app_id": "2277560",
        "limit": 100
    }
)
reviews = response.json()

# 获取统计
stats = requests.get(
    f"{BASE_URL}/stats",
    params={"app_id": "2277560"}
).json()

print(f"正面率: {stats['positive_rate']:.1%}")
print(f"总评论数: {stats['total_reviews']}")

# 导出数据
csv_data = requests.get(
    f"{BASE_URL}/export/csv",
    params={"app_id": "2277560"}
)
with open("reviews.csv", "wb") as f:
    f.write(csv_data.content)
```

### 创建包装类

```python
class SteamReviewClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def get_reviews(self, app_id, limit=100, offset=0):
        resp = requests.get(
            f"{self.base_url}/reviews",
            params={
                "app_id": app_id,
                "limit": limit,
                "offset": offset
            }
        )
        return resp.json()
    
    def get_stats(self, app_id=None):
        params = {"app_id": app_id} if app_id else {}
        resp = requests.get(f"{self.base_url}/stats", params=params)
        return resp.json()
    
    def export(self, format, app_id=None):
        resp = requests.get(
            f"{self.base_url}/export/{format}",
            params={"app_id": app_id} if app_id else {}
        )
        return resp.content

# 使用
client = SteamReviewClient()
reviews = client.get_reviews("2277560", limit=50)
stats = client.get_stats("2277560")
```

## JavaScript/TypeScript 示例

```javascript
const BASE_URL = "http://localhost:8000";

// 获取评论
async function getReviews(appId, limit = 100) {
  const response = await fetch(
    `${BASE_URL}/reviews?app_id=${appId}&limit=${limit}`
  );
  return response.json();
}

// 获取统计
async function getStats(appId) {
  const response = await fetch(`${BASE_URL}/stats?app_id=${appId}`);
  return response.json();
}

// 导出数据
async function exportData(format, appId) {
  const response = await fetch(
    `${BASE_URL}/export/${format}?app_id=${appId}`
  );
  return response.blob();
}

// 使用
(async () => {
  const reviews = await getReviews("2277560");
  const stats = await getStats("2277560");
  console.log(`Positive rate: ${(stats.positive_rate * 100).toFixed(1)}%`);
})();
```

## 认证

当前版本的 API 不需要认证。所有端点都是公开的。

（在未来版本中可能会添加 API 密钥认证）

## 速率限制

当前版本不强制执行速率限制。建议：
- 单个请求不超过 1000 条记录
- 避免重复频繁的大量请求
- 使用缓存/本地存储避免重复请求

## CORS

API 启用了 CORS，支持来自任何域的跨域请求。

## 性能提示

1. **使用分页**: 不要一次请求所有数据，使用 `limit` 和 `offset`
2. **缓存结果**: 本地缓存 API 响应
3. **使用导出**: 对于大量数据，使用导出端点而不是逐个请求

## 版本控制

当前 API 版本: **v1.0**

未来计划添加:
- API v2 with GraphQL support
- WebSocket for real-time updates
- Authentication & API keys

---

更多帮助: [文档首页](./README.md) | [仪表板指南](./04-dashboard-guide.md)
