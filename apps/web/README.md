# Cyber Werewolves Web Frontend

人机混战狼人杀游戏平台的前端应用，基于 Vue 3 + TypeScript + Arco Design 构建。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - JavaScript 的类型化超集
- **Arco Design** - 企业级设计语言和 Vue 组件库
- **Vite** - 下一代前端构建工具
- **Pinia** - Vue 状态管理库
- **Vue Router** - Vue.js 官方路由器
- **Socket.io Client** - 实时通信客户端

## 功能特性

### 核心功能
- 🎮 实时多人狼人杀游戏
- 🤖 AI 智能体支持
- 💬 实时聊天和通信
- 🏠 房间创建和管理
- 👥 用户认证和管理

### UI 组件 (按 D02 规范实现)
- **TimelineView** - 虚拟滚动时间线组件，支持 10k+ 消息
- **MessageBubble** - 消息气泡组件，支持流式输出
- **PhaseBanner** - 游戏阶段横幅，带倒计时
- **ActionPanel** - 玩家操作面板
- **SystemToast** - 系统通知组件

### 技术特性
- 📱 响应式设计，支持移动端
- ♿ 无障碍访问 (WCAG AA 标准)
- 🌐 WebSocket 实时通信
- 🎨 主题定制和深色模式支持
- ⚡ 虚拟滚动优化性能
- 🔄 自动重连和错误恢复

## 项目结构

```
src/
├── components/          # 组件
│   ├── Game/           # 游戏相关组件
│   └── Timeline/       # 时间线组件
├── views/              # 页面视图
├── stores/             # Pinia 状态管理
├── services/           # API 和 WebSocket 服务
├── types/              # TypeScript 类型定义
├── utils/              # 工具函数
├── styles/             # 全局样式
└── router/             # 路由配置
```

## 开发指南

### 环境要求

- Node.js 16+
- npm 或 yarn

### 安装依赖

```bash
npm install
```

### 开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

### 类型检查

```bash
npm run type-check
```

### 代码检查

```bash
npm run lint
```

## 配置

### 环境变量

在 `.env` 文件中配置：

```env
# API 配置
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# 应用配置
VITE_APP_TITLE=Cyber Werewolves
VITE_APP_DESCRIPTION=人机混战狼人杀游戏平台
```

### 代理配置

Vite 配置了 API 代理：
- `/api/*` → `http://localhost:8000/*`
- `/ws` → `ws://localhost:8000/ws`

## API 集成

### 后端接口

- **认证**: `/auth/login`, `/auth/register`
- **房间管理**: `/rooms`, `/rooms/create`
- **WebSocket**: `/ws`

### WebSocket 事件

- `game_event` - 游戏事件
- `room_update` - 房间更新
- `player_update` - 玩家更新
- `error` - 错误信息

## 组件使用

### TimelineView

```vue
<template>
  <TimelineView
    :messages="timelineMessages"
    :auto-scroll="true"
    @load-more="loadMoreMessages"
  />
</template>
```

### MessageBubble

```vue
<template>
  <MessageBubble
    :id="message.id"
    :author-name="message.authorName"
    :content="message.content"
    :visibility="message.visibility"
    :timestamp="message.timestamp"
  />
</template>
```

### PhaseBanner

```vue
<template>
  <PhaseBanner
    :phase="currentPhase"
    :time-remaining="timeRemaining"
    :title="phaseTitle"
    :description="phaseDescription"
  />
</template>
```

## 状态管理

使用 Pinia 进行状态管理：

- **authStore** - 用户认证状态
- **gameStore** - 游戏状态和消息

## 路由结构

- `/` - 首页
- `/auth/login` - 登录
- `/auth/register` - 注册
- `/rooms` - 房间列表
- `/rooms/create` - 创建房间
- `/room/:id` - 游戏房间
- `/profile` - 个人中心

## 无障碍访问

- ✅ 键盘导航支持
- ✅ 屏幕阅读器兼容
- ✅ ARIA 属性完整
- ✅ 颜色对比度符合 WCAG AA
- ✅ 焦点管理
- ✅ 语义化 HTML

## 性能优化

- 虚拟滚动处理大量消息
- 组件懒加载
- 图片懒加载
- WebSocket 连接池
- 本地缓存优化

## 浏览器支持

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 部署

### Docker 部署

```dockerfile
FROM node:16-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 静态部署

构建后将 `dist` 目录部署到任意静态文件服务器。

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。