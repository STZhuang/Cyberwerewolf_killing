/**
 * Vue Router configuration
 */

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores'

// Route components (lazy-loaded)
const Home = () => import('@/views/Home.vue')
const Login = () => import('@/views/Auth/Login.vue')
const Register = () => import('@/views/Auth/Register.vue')
const RoomList = () => import('@/views/Room/RoomList.vue')
const CreateRoom = () => import('@/views/Room/CreateRoom.vue')
const GameRoom = () => import('@/views/Game/GameRoom.vue')
const Profile = () => import('@/views/Profile.vue')
const Settings = () => import('@/views/Settings/index.vue')
const NotFound = () => import('@/views/NotFound.vue')

// Route definitions
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: {
      title: '首页'
    }
  },
  {
    path: '/auth',
    name: 'auth',
    redirect: '/auth/login',
    children: [
      {
        path: 'login',
        name: 'login',
        component: Login,
        meta: {
          title: '登录',
          requiresGuest: true
        }
      },
      {
        path: 'register',
        name: 'register',
        component: Register,
        meta: {
          title: '注册',
          requiresGuest: true
        }
      }
    ]
  },
  {
    path: '/rooms',
    name: 'rooms',
    component: RoomList,
    meta: {
      title: '房间列表',
      requiresAuth: true
    }
  },
  {
    path: '/rooms/create',
    name: 'create-room',
    component: CreateRoom,
    meta: {
      title: '创建房间',
      requiresAuth: true
    }
  },
  {
    path: '/room/:id',
    name: 'game-room',
    component: GameRoom,
    meta: {
      title: '游戏房间',
      requiresAuth: true
    },
    props: true
  },
  {
    path: '/profile',
    name: 'profile',
    component: Profile,
    meta: {
      title: '个人中心',
      requiresAuth: true
    }
  },
  {
    path: '/settings',
    name: 'settings',
    component: Settings,
    meta: {
      title: '设置',
      requiresAuth: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: NotFound,
    meta: {
      title: '页面未找到'
    }
  }
]

// Create router instance
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // Initialize auth store if not done already
  if (!authStore.isAuthenticated && authStore.token) {
    try {
      await authStore.init()
    } catch (error) {
      console.error('Failed to initialize auth:', error)
    }
  }

  // Check if route requires authentication
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    // Redirect to login page
    next({
      name: 'login',
      query: { redirect: to.fullPath }
    })
    return
  }

  // Check if route requires guest (unauthenticated user)
  if (to.meta.requiresGuest && authStore.isLoggedIn) {
    // Redirect to home page
    next({ name: 'home' })
    return
  }

  // Set document title
  if (to.meta.title) {
    document.title = `${to.meta.title} - Cyber Werewolves`
  } else {
    document.title = 'Cyber Werewolves - 人机混战狼人杀'
  }

  next()
})

// Handle router errors
router.onError((error) => {
  console.error('Router error:', error)
  
  // Handle chunk load errors (when lazy-loaded components fail to load)
  if (error.message?.includes('Loading chunk') || error.message?.includes('Failed to fetch')) {
    // Reload the page to recover from chunk loading errors
    window.location.reload()
  }
})

export default router

// Type augmentation for route meta
declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    requiresGuest?: boolean
    layout?: string
  }
}