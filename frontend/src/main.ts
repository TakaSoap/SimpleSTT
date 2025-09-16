import { createApp } from 'vue'
import naive from 'naive-ui'
import App from './App.vue'
import router from './router'
import { i18n } from './i18n'

createApp(App).use(router).use(naive).use(i18n).mount('#app')
