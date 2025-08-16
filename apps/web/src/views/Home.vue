<template>
  <div class="home">
    <!-- Hero section -->
    <header class="hero">
      <div class="hero-content">
        <h1 class="hero-title">Cyber Werewolves</h1>
        <p class="hero-subtitle">人机混战狼人杀</p>
        <p class="hero-description">
          体验创新的人机混战狼人杀游戏，与AI智能体同台竞技，感受全新的游戏乐趣
        </p>
        
        <div class="hero-actions">
          <AButton 
            v-if="!authStore.isLoggedIn" 
            type="primary" 
            size="large"
            @click="router.push('/auth/login')"
          >
            开始游戏
          </AButton>
          <AButton 
            v-else 
            type="primary" 
            size="large"
            @click="router.push('/rooms')"
          >
            进入游戏
          </AButton>
          <AButton size="large" @click="scrollToFeatures">
            了解更多
          </AButton>
        </div>
      </div>
      
      <div class="hero-visual">
        <div class="game-preview">
          <!-- Placeholder for game screenshot or animation -->
          <div class="preview-placeholder">
            <AIcon icon="icon-gamepad" class="preview-icon" />
          </div>
        </div>
      </div>
    </header>

    <!-- Features section -->
    <section ref="featuresRef" class="features">
      <div class="container">
        <h2 class="section-title">游戏特色</h2>
        
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">
              <AIcon icon="icon-robot" />
            </div>
            <h3 class="feature-title">AI智能体</h3>
            <p class="feature-description">
              与高智能AI玩家同台竞技，体验更加刺激有趣的游戏对局
            </p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <AIcon icon="icon-message" />
            </div>
            <h3 class="feature-title">实时通讯</h3>
            <p class="feature-description">
              基于WebSocket的实时消息系统，支持公开讨论和队伍私聊
            </p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <AIcon icon="icon-timeline" />
            </div>
            <h3 class="feature-title">时间线UI</h3>
            <p class="feature-description">
              创新的时间线界面，完整记录游戏过程，支持虚拟滚动优化性能
            </p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <AIcon icon="icon-settings" />
            </div>
            <h3 class="feature-title">灵活配置</h3>
            <p class="feature-description">
              支持多种角色配置和游戏规则，满足不同玩家的游戏需求
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats section -->
    <section class="stats">
      <div class="container">
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-number">1000+</div>
            <div class="stat-label">游戏场次</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">500+</div>
            <div class="stat-label">活跃玩家</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">24/7</div>
            <div class="stat-label">在线服务</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">100%</div>
            <div class="stat-label">免费游戏</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <div class="container">
        <div class="footer-content">
          <div class="footer-info">
            <h3>Cyber Werewolves</h3>
            <p>人机混战狼人杀游戏平台</p>
          </div>
          
          <div class="footer-links">
            <div class="link-group">
              <h4>游戏</h4>
              <AButton type="text" size="small" @click="router.push('/rooms')">
                房间列表
              </AButton>
              <AButton type="text" size="small" @click="router.push('/rooms/create')">
                创建房间
              </AButton>
            </div>
            
            <div class="link-group">
              <h4>账户</h4>
              <AButton 
                v-if="!authStore.isLoggedIn"
                type="text" 
                size="small" 
                @click="router.push('/auth/login')"
              >
                登录
              </AButton>
              <AButton 
                v-if="!authStore.isLoggedIn"
                type="text" 
                size="small" 
                @click="router.push('/auth/register')"
              >
                注册
              </AButton>
              <AButton 
                v-if="authStore.isLoggedIn"
                type="text" 
                size="small" 
                @click="router.push('/profile')"
              >
                个人中心
              </AButton>
            </div>
          </div>
        </div>
        
        <div class="footer-bottom">
          <p>&copy; 2024 Cyber Werewolves. All rights reserved.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { AButton, AIcon } from '@arco-design/web-vue'
import { useAuthStore } from '@/stores'

const router = useRouter()
const authStore = useAuthStore()

const featuresRef = ref<HTMLElement>()

function scrollToFeatures() {
  featuresRef.value?.scrollIntoView({ behavior: 'smooth' })
}
</script>

<style scoped lang="scss">
.home {
  min-height: 100vh;
}

.hero {
  min-height: 80vh;
  display: flex;
  align-items: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, var(--color-primary-1) 0%, var(--color-primary-2) 100%);
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E") repeat;
    opacity: 0.5;
  }

  .hero-content {
    flex: 1;
    max-width: 600px;
    z-index: 1;
    position: relative;
  }

  .hero-visual {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1;
    position: relative;
  }
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  margin: 0 0 16px 0;
  background: linear-gradient(135deg, var(--color-primary-6), var(--color-purple-6));
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.1;
}

.hero-subtitle {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 20px 0;
  color: var(--color-text-2);
}

.hero-description {
  font-size: 1.1rem;
  line-height: 1.6;
  margin: 0 0 32px 0;
  color: var(--color-text-2);
}

.hero-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.game-preview {
  width: 400px;
  height: 300px;
  background: var(--color-bg-2);
  border: 1px solid var(--color-neutral-3);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.preview-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(45deg, var(--color-neutral-1), var(--color-neutral-2));
}

.preview-icon {
  font-size: 80px;
  color: var(--color-text-3);
  opacity: 0.3;
}

.features {
  padding: 80px 20px;
  background: var(--color-bg-2);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.section-title {
  font-size: 2.5rem;
  font-weight: 700;
  text-align: center;
  margin: 0 0 60px 0;
  color: var(--color-text-1);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 32px;
}

.feature-card {
  background: var(--color-bg-1);
  border: 1px solid var(--color-neutral-3);
  border-radius: 12px;
  padding: 32px 24px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  }
}

.feature-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, var(--color-primary-6), var(--color-purple-6));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;

  .arco-icon {
    font-size: 28px;
    color: white;
  }
}

.feature-title {
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: var(--color-text-1);
}

.feature-description {
  font-size: 1rem;
  line-height: 1.6;
  margin: 0;
  color: var(--color-text-2);
}

.stats {
  padding: 60px 20px;
  background: var(--color-primary-1);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 40px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 3rem;
  font-weight: 800;
  color: var(--color-primary-6);
  margin-bottom: 8px;
  line-height: 1;
}

.stat-label {
  font-size: 1.1rem;
  color: var(--color-text-2);
  font-weight: 500;
}

.footer {
  background: var(--color-bg-3);
  border-top: 1px solid var(--color-neutral-3);
  padding: 60px 20px 20px;
}

.footer-content {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 60px;
  margin-bottom: 40px;
}

.footer-info {
  h3 {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0 0 12px 0;
    color: var(--color-text-1);
  }

  p {
    margin: 0;
    color: var(--color-text-2);
    font-size: 1rem;
  }
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 40px;
}

.link-group {
  h4 {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0 0 16px 0;
    color: var(--color-text-1);
  }

  .arco-btn {
    display: block;
    text-align: left;
    color: var(--color-text-2);
    margin-bottom: 8px;

    &:hover {
      color: var(--color-primary-6);
    }
  }
}

.footer-bottom {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid var(--color-neutral-3);

  p {
    margin: 0;
    color: var(--color-text-3);
    font-size: 0.9rem;
  }
}

// Responsive design
@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    text-align: center;
    padding: 40px 20px;

    .hero-content {
      margin-bottom: 40px;
    }
  }

  .hero-title {
    font-size: 2.5rem;
  }

  .hero-subtitle {
    font-size: 1.2rem;
  }

  .hero-description {
    font-size: 1rem;
  }

  .game-preview {
    width: 100%;
    max-width: 350px;
    height: 250px;
  }

  .section-title {
    font-size: 2rem;
  }

  .features-grid {
    gap: 24px;
  }

  .feature-card {
    padding: 24px 20px;
  }

  .stats-grid {
    gap: 24px;
  }

  .stat-number {
    font-size: 2.5rem;
  }

  .footer-content {
    grid-template-columns: 1fr;
    gap: 40px;
    text-align: center;
  }

  .footer-links {
    justify-items: center;
  }
}

// Dark theme
@media (prefers-color-scheme: dark) {
  .hero {
    background: linear-gradient(135deg, var(--color-neutral-9) 0%, var(--color-neutral-8) 100%);
  }
}
</style>