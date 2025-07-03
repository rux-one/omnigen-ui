import { createApp } from 'vue'
import App from './App.vue'
import ToastPlugin from 'vue-toast-notification'
import 'vue-toast-notification/dist/theme-default.css'

const app = createApp(App)

// Register plugins
app.use(ToastPlugin, {
  position: 'top-right',
  duration: 3000
})

// Mount the app
app.mount('#app')
