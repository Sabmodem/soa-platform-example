import { h, createApp } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'

import App from './components/FileStorageComponent.vue'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light'
  }
})

export default {
  name: 'FederationWrapper',  
  props: {
    apiClient: {
      type: Object,
      default: null
    }
  },
  
  async beforeCreate() {
    const app = this.$.appContext.app
    if (!app.config.globalProperties.$vuetify) {
      console.log('Vuetify не найден, устанавливаем...')
      app.use(vuetify)
    } else {
      console.log('Vuetify уже установлен в хосте')
    }
    try {
      let apiClient = this.apiClient
      if (!apiClient) {
        const { getApiClient } = await import('main-ui/ApiClient')
        let retries = 0
        const maxRetries = 10        
        while (retries < maxRetries) {
          try {
            apiClient = getApiClient()
            break
          } catch (error) {
            retries++
            await new Promise(resolve => setTimeout(resolve, 100))
          }
        }
        
        if (!apiClient) {
          throw new Error('Не удалось получить API клиент от host приложения')
        }
      }
      const app = this.$.appContext.app
      app.config.globalProperties.$api = apiClient
      app.provide('apiClient', apiClient)      
    } catch (error) {
      console.error(error)
    }
    
  },
      
  render() {
    return h(App)
  },
  
  async mount(selector) {
    const app = createApp(this)
    app.use(vuetify)
    if (this.apiClient) {
      app.config.globalProperties.$api = this.apiClient
      app.provide('apiClient', this.apiClient)
    }    
    return app.mount(selector)
  }
}