# 🚀 Cyber Werewolves 启动指南

## 📋 前置要求

- Docker & Docker Compose
- Node.js 16+
- Python 3.9+
- Git

## 🎯 启动方式（分离部署）

### 方法一：使用启动脚本（推荐）

```bash
# Windows
.\scripts\start-infra.bat     # 启动基础设施
.\scripts\start-api.bat       # 启动后端API
.\scripts\start-agents.bat    # 启动Agent服务
.\scripts\start-web.bat       # 启动前端

# Linux/macOS
./scripts/start-infra.sh      # 启动基础设施
./scripts/start-api.sh        # 启动后端API
./scripts/start-agents.sh     # 启动Agent服务
./scripts/start-web.sh        # 启动前端
```

### 方法二：手动启动

#### 1. 启动基础设施（Docker）
```bash
# 启动 PostgreSQL + Redis
docker-compose -f docker-compose.infra.yml up -d postgres redis

# 可选：启动管理工具
docker-compose -f docker-compose.infra.yml --profile with-pgadmin up -d pgadmin
docker-compose -f docker-compose.infra.yml --profile with-redis-gui up -d redis-commander
```

#### 2. 启动后端API（Python）
```bash
cd apps/api
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 启动Agent服务（Python）
```bash
cd apps/agents
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

#### 4. 启动前端（Vue.js）
```bash
cd apps/web
npm install
npm run dev
```

## 🔧 配置说明

### 环境变量配置
复制 `.env` 文件并修改必要的配置：

```bash
# 基础设施配置（必需）
JWT_SECRET=your-very-secure-jwt-secret-key-here-at-least-32-characters
POSTGRES_PASSWORD=your-secure-password
DATABASE_URL=postgresql://werewolves:your-secure-password@localhost:5432/cyber_werewolves
REDIS_URL=redis://localhost:6379
```

### LLM 配置（前端界面配置）
**重要：本项目不使用 .env 文件配置 LLM！**

所有 LLM 配置（API Key、模型ID、Base URL）都通过前端界面进行：

1. 启动应用并登录
2. 点击右下角浮动菜单
3. 进入"设置" > "LLM 模型配置"
4. 配置您的 LLM 服务：

```
# OpenAI 配置示例
模型ID: gpt-4o-mini
API Key: sk-your-openai-key
Base URL: https://api.openai.com/v1

# 本地 Ollama 配置示例
模型ID: llama3.1:8b
API Key: ollama
Base URL: http://localhost:11434/v1

# 自定义 API 配置示例
模型ID: your-model-name
API Key: your-api-key
Base URL: https://your-api-endpoint/v1
```

## 📊 服务端口

| 服务 | 端口 | 用途 |
|------|------|------|
| 前端 | 3000 | Vue.js 应用 |
| 后端API | 8000 | FastAPI 服务 |
| Agent服务 | 8001 | LLM Agent 管理 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |
| PgAdmin | 5050 | 数据库管理（可选） |
| Redis GUI | 8081 | Redis 管理（可选） |

## 🔍 验证启动

```bash
# API 健康检查
curl http://localhost:8000/health

# Agent 服务检查
curl http://localhost:8001/

# 前端访问
http://localhost:3000
```

## 🎮 使用流程

1. **访问应用**：http://localhost:3000
2. **注册/登录**：创建账户
3. **配置LLM**：设置 > LLM模型配置
4. **测试连接**：确保LLM服务可用
5. **创建房间**：开始游戏
6. **添加AI玩家**：使用配置的LLM创建AI玩家

## 🛠️ 常见问题

### Docker 网络冲突
```bash
docker network prune -f
```

### 端口占用
修改 `.env` 文件中的端口配置

### LLM 连接失败
1. 检查 API Key 是否正确
2. 确认 Base URL 格式
3. 验证网络连接
4. 查看测试连接错误信息

### 数据库连接问题
```bash
# 检查PostgreSQL容器状态
docker-compose -f docker-compose.infra.yml ps postgres

# 查看日志
docker-compose -f docker-compose.infra.yml logs postgres
```

## 🔄 停止服务

```bash
# 停止基础设施
docker-compose -f docker-compose.infra.yml down

# 手动停止其他服务（Ctrl+C）
```

## 🎯 特性说明

- **人机混战**：人类玩家 + AI 玩家同台竞技
- **动态LLM配置**：前端界面自由切换LLM服务
- **实时通信**：WebSocket 实时游戏状态同步
- **角色多样**：支持狼人、预言家、女巫、守卫等多种角色
- **审计追踪**：完整的游戏事件记录
- **响应式设计**：支持桌面和移动设备