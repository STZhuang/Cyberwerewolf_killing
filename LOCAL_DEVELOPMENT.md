# 本地开发指南

这份指南将帮助你在本地环境中分层启动赛博狼人杀项目，便于开发和调试。

## 🏗️ 架构概览

项目采用微服务架构，可以分层启动：

```
┌─────────────────────────────────────────────────────────┐
│                    本地开发架构                            │
├─────────────────────────────────────────────────────────┤
│  Frontend (Vue.js)     │  npm run dev  │  :3000        │
│  API (FastAPI)         │  uvicorn      │  :8000        │  
│  Agents (Agno)         │  uvicorn      │  :8001        │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL (Docker)   │  postgres     │  :5432        │
│  Redis (Docker)        │  redis        │  :6379        │
│  NATS (Docker)         │  nats         │  :4222        │
└─────────────────────────────────────────────────────────┘
```

## 🚀 快速启动

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd Cyber_Werewolves

# 复制环境配置
cp .env.local .env

# 编辑 .env 文件，添加必要的API密钥
# 必须配置: OPENAI_API_KEY, ANTHROPIC_API_KEY
```

### 2. 启动基础设施 (Docker)

**Linux/Mac:**
```bash
# 启动PostgreSQL + Redis
./scripts/start-infra.sh

# 可选: 启动管理工具
docker-compose -f docker-compose.infra.yml --profile with-pgadmin up -d pgadmin
docker-compose -f docker-compose.infra.yml --profile with-redis-gui up -d redis-commander
```

**Windows:**
```cmd
# 启动PostgreSQL + Redis  
scripts\start-infra.bat

# 可选: 启动管理工具
docker-compose -f docker-compose.infra.yml --profile with-pgadmin up -d pgadmin
docker-compose -f docker-compose.infra.yml --profile with-redis-gui up -d redis-commander
```

### 3. 启动应用服务

打开3个终端，分别启动：

**Terminal 1 - API服务:**
```bash
# Linux/Mac
./scripts/start-api.sh

# Windows  
scripts\start-api.bat
```

**Terminal 2 - Agent服务:**
```bash
# Linux/Mac
./scripts/start-agents.sh

# Windows
scripts\start-agents.bat
```

**Terminal 3 - 前端:**
```bash
# Linux/Mac
./scripts/start-web.sh

# Windows
scripts\start-web.bat
```

### 4. 验证服务

打开浏览器访问：
- 前端应用: http://localhost:3000
- API文档: http://localhost:8000/docs
- Agent服务: http://localhost:8001
- PgAdmin: http://localhost:5050 (如果启用)
- Redis GUI: http://localhost:8081 (如果启用)

## 📁 项目结构

```
Cyber_Werewolves/
├── apps/
│   ├── api/                # FastAPI后端
│   │   ├── app/
│   │   ├── requirements.txt
│   │   └── ...
│   ├── agents/             # Agno智能体服务
│   │   ├── agents/
│   │   ├── tools/
│   │   ├── requirements.txt
│   │   └── ...
│   └── web/                # Vue.js前端
│       ├── src/
│       ├── package.json
│       └── ...
├── packages/               # 共享包
│   └── sdk-py/
├── scripts/                # 启动脚本
├── docker-compose.infra.yml # 基础设施Docker配置
├── .env.local              # 本地开发环境模板
└── LOCAL_DEVELOPMENT.md    # 本文档
```

## 🔧 开发工具

### Python 虚拟环境

每个Python服务会自动创建虚拟环境：
```bash
# API服务
cd apps/api
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Agent服务
cd apps/agents  
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 数据库管理

**使用PgAdmin (推荐):**
```bash
docker-compose -f docker-compose.infra.yml --profile with-pgadmin up -d pgadmin
# 访问: http://localhost:5050
# 登录: admin@werewolves.local / admin
```

**使用命令行:**
```bash
# 连接数据库
psql -h localhost -p 5432 -U werewolves -d cyber_werewolves

# 查看表结构
\dt
\d users
```

### Redis管理

**使用Redis Commander:**
```bash
docker-compose -f docker-compose.infra.yml --profile with-redis-gui up -d redis-commander
# 访问: http://localhost:8081
# 登录: admin / admin
```

**使用命令行:**
```bash
redis-cli -h localhost -p 6379
# 查看所有键
KEYS *
```

## 🐞 调试技巧

### 1. 查看日志

每个服务都有详细的日志输出：

```bash
# API服务日志 (在API终端)
# 所有请求都会显示在控制台

# Agent服务日志 (在Agent终端) 
# Agent决策过程会输出到控制台

# 前端日志 (浏览器开发者工具)
# 按F12打开开发者工具查看网络请求
```

### 2. 热重载

所有服务都支持热重载：
- **API**: 修改Python文件后自动重启
- **Agents**: 修改Python文件后自动重启  
- **Frontend**: 修改Vue文件后自动刷新

### 3. 断点调试

**Python服务 (VS Code):**
1. 在VS Code中打开项目
2. 设置断点
3. 使用调试配置启动服务

**Frontend (浏览器):**
1. 在浏览器开发者工具中设置断点
2. 或在Vue文件中使用 `debugger;`

## ⚙️ 环境配置

### 必需的API密钥

编辑 `.env` 文件：

```bash
# OpenAI (必需)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Anthropic (可选，用于Claude模型)  
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Google (可选，用于Gemini模型)
GOOGLE_API_KEY=your-google-ai-api-key-here
```

### 数据库配置

默认配置已经优化用于本地开发：

```bash
POSTGRES_DB=cyber_werewolves
POSTGRES_USER=werewolves
POSTGRES_PASSWORD=dev_password_123
DATABASE_URL=postgresql://werewolves:dev_password_123@localhost:5432/cyber_werewolves
```

### 端口配置

默认端口分配：

```bash
API_PORT=8000          # FastAPI
AGENT_PORT=8001        # Agno Agents
WEB_PORT=3000          # Vue.js Dev Server
POSTGRES_PORT=5432     # PostgreSQL
REDIS_PORT=6379        # Redis
```

## 🔄 常用操作

### 重置数据库

```bash
# 停止所有服务
docker-compose -f docker-compose.infra.yml down -v

# 重新启动
./scripts/start-infra.sh  # 或 scripts\start-infra.bat
```

### 清理环境

```bash
# 删除Docker卷
docker-compose -f docker-compose.infra.yml down -v

# 删除Python虚拟环境
rm -rf apps/api/venv apps/agents/venv

# 删除Node模块 
rm -rf apps/web/node_modules
```

### 更新依赖

```bash
# Python依赖
cd apps/api && pip install -r requirements.txt --upgrade
cd apps/agents && pip install -r requirements.txt --upgrade

# Node.js依赖
cd apps/web && npm update
```

## 📝 开发工作流

1. **启动基础设施**: `./scripts/start-infra.sh`
2. **启动API服务**: `./scripts/start-api.sh`
3. **启动Agent服务**: `./scripts/start-agents.sh`  
4. **启动前端**: `./scripts/start-web.sh`
5. **开始开发**: 修改代码，服务会自动重载
6. **测试功能**: 在浏览器中测试游戏功能
7. **查看日志**: 在各个终端中查看实时日志

## ❓ 常见问题

### Q: API服务启动失败
A: 检查PostgreSQL是否启动，端口是否被占用

### Q: Agent服务报API Key错误  
A: 确保在 `.env` 文件中配置了有效的API密钥

### Q: 前端无法连接后端
A: 检查API服务是否运行在正确端口，防火墙设置

### Q: 数据库连接失败
A: 确保Docker服务运行正常，数据库密码正确

### Q: 热重载不工作
A: 检查文件监听权限，重启对应服务

## 🛠️ 生产部署

开发完成后，可以使用完整的Docker Compose进行生产部署：

```bash
# 生产环境部署
docker-compose --profile production up -d

# 监控环境部署  
docker-compose --profile monitoring up -d
```

更多生产部署信息请参考主 `README.md` 文件。