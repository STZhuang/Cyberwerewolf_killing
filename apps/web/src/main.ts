/**
 * Main application entry point
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ArcoVue from '@arco-design/web-vue'
import ArcoVueIcon from '@arco-design/web-vue/es/icon'
import router from './router'
import App from './App.vue'

// Import Arco Design styles
import '@arco-design/web-vue/dist/arco.css'

// Import global styles
import '@/styles/global.scss'

// Create Vue app
const app = createApp(App)

// Install plugins
app.use(createPinia())
app.use(router)
app.use(ArcoVue)
app.use(ArcoVueIcon)

// Global error handler
app.config.errorHandler = (error, instance, info) => {
  console.error('Vue error:', error, info)
  
  // In production, you might want to send errors to a logging service
  if (import.meta.env.PROD) {
    // Send to error tracking service (e.g., Sentry)
    console.error('Production error:', { error, info })
  }
}

// Mount app
app.mount('#app')