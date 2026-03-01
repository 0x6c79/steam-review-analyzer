# 项目文档

欢迎来到 Steam Review Analyzer 的文档中心。本项目提供了全面的文档来帮助用户、开发者和管理员理解和使用本系统。

## 📚 文档导航

### 🚀 快速开始
- **[快速开始指南](./01-getting-started.md)** - 5分钟内快速上手
- **[安装指南](./01-getting-started.md#安装)** - 详细的安装说明

### 📖 核心指南
- **[使用指南](./02-user-guide.md)** - 如何使用各项功能
- **[API 文档](./03-api-reference.md)** - API 端点和用法
- **[仪表板指南](./04-dashboard-guide.md)** - 仪表板功能和特性

### 🏗️ 架构与设计
- **[系统架构](./05-architecture.md)** - 系统设计和组件
- **[数据库设计](./06-database-schema.md)** - 数据库架构和查询
- **[数据流程](./05-architecture.md#数据流程)** - 数据从采集到可视化的流程

### ⚡ 性能与优化
- **[性能优化指南](./07-performance.md)** - 启动优化和缓存策略
- **[部署指南](./08-deployment.md)** - Docker 和生产部署

### 🔬 高级功能
- **[高级分析](./09-advanced-analytics.md)** - 高级分析功能
- **[主题建模](./05-architecture.md#分析模块)** - LDA 和主题分析

### 👥 贡献指南
- **[贡献指南](./10-contributing.md)** - 如何参与项目贡献
- **[开发环境设置](./10-contributing.md#开发环境设置)** - 开发者工作流
- **[路线图](./11-roadmap.md)** - 项目发展方向

### 🔧 其他资源
- **[常见问题](./12-faq.md)** - 常见问题解答
- **[变更日志](./13-changelog.md)** - 版本历史

## 🎯 快速链接

### 我想...

| 任务 | 文档 |
|------|------|
| 快速上手 | [快速开始](./01-getting-started.md) |
| 爬取Steam评论 | [使用指南 - 爬虫](./02-user-guide.md#数据爬取) |
| 分析评论数据 | [使用指南 - 分析](./02-user-guide.md#数据分析) |
| 查看仪表板 | [仪表板指南](./04-dashboard-guide.md) |
| 使用 API | [API 文档](./03-api-reference.md) |
| 理解架构 | [系统架构](./05-architecture.md) |
| 优化性能 | [性能指南](./07-performance.md) |
| 部署到生产 | [部署指南](./08-deployment.md) |
| 贡献代码 | [贡献指南](./10-contributing.md) |
| 了解未来计划 | [路线图](./11-roadmap.md) |

## 📋 文档组织

```
docs/
├── README.md                          # 您在这里
├── 01-getting-started.md             # 快速开始和安装
├── 02-user-guide.md                  # 使用指南
├── 03-api-reference.md               # API 文档
├── 04-dashboard-guide.md             # 仪表板指南
├── 05-architecture.md                # 系统架构
├── 06-database-schema.md             # 数据库设计
├── 07-performance.md                 # 性能优化
├── 08-deployment.md                  # 部署指南
├── 09-advanced-analytics.md          # 高级分析
├── 10-contributing.md                # 贡献指南
├── 11-roadmap.md                     # 路线图
├── 12-faq.md                         # 常见问题
└── 13-changelog.md                   # 变更日志
```

## 👥 针对不同角色的建议

### 👤 用户
如果您想使用本项目来分析Steam游戏评论，请按以下顺序阅读：
1. [快速开始](./01-getting-started.md)
2. [使用指南](./02-user-guide.md)
3. [仪表板指南](./04-dashboard-guide.md)

### 🧑‍💻 开发者
如果您想理解代码结构和贡献代码，请按以下顺序阅读：
1. [快速开始](./01-getting-started.md)
2. [贡献指南](./10-contributing.md)
3. [系统架构](./05-architecture.md)
4. [数据库设计](./06-database-schema.md)

### 🔌 API 使用者
如果您想集成本项目的 API，请阅读：
1. [快速开始](./01-getting-started.md)
2. [API 文档](./03-api-reference.md)

### 🚀 DevOps / 部署人员
如果您要部署本项目到生产环境，请阅读：
1. [部署指南](./08-deployment.md)
2. [性能优化](./07-performance.md)
3. [系统架构](./05-architecture.md)

## ❓ 需要帮助？

- **问题或建议**: 打开 [GitHub Issue](https://github.com/0x6c79/steam-review-analyzer/issues)
- **讨论**: 使用 [GitHub Discussions](https://github.com/0x6c79/steam-review-analyzer/discussions)
- **贡献代码**: 查看 [贡献指南](./10-contributing.md)

## 📝 文档版本

- **最后更新**: 2026-03-01
- **适用版本**: v1.0.0+
- **Python版本**: 3.12+

---

**提示**: 使用 Ctrl+F (Windows/Linux) 或 Cmd+F (Mac) 来搜索文档内容。
