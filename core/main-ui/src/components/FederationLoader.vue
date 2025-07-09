// Обновленный FederationLoader.vue для поддержки API клиента
// components/FederationLoader.vue
<template>
  <div class="federation-loader">
    <!-- Состояние загрузки -->
    <v-skeleton-loader 
      v-if="loading" 
      type="article"
      class="ma-4"
    ></v-skeleton-loader>
    
    <!-- Ошибка загрузки -->
    <v-alert 
      v-else-if="error" 
      type="error" 
      variant="tonal"
      class="ma-4"
    >
      <v-alert-title>Ошибка загрузки сервиса</v-alert-title>
      <div>{{ error.message }}</div>
      <template v-slot:append>
        <v-btn 
          variant="outlined" 
          size="small" 
          @click="retryLoad"
        >
          Повторить
        </v-btn>
      </template>
    </v-alert>
    
    <!-- Сервис не найден -->
    <v-alert 
      v-else-if="!currentComponent && serviceName" 
      type="warning"
      variant="tonal"
      class="ma-4"
    >
      <v-alert-title>Сервис не найден</v-alert-title>
      <div>Сервис "{{ serviceName }}" не зарегистрирован или недоступен</div>
    </v-alert>
    
    <!-- Загруженный компонент с передачей API клиента -->
    <component 
      v-else-if="currentComponent"
      :is="currentComponent"
      :api-client="apiClient"
      v-bind="componentProps"
      @service-event="handleServiceEvent"
    />
    
    <!-- Пустое состояние -->
    <v-container v-else class="text-center">
      <v-icon size="64" color="grey-lighten-1">mdi-application-outline</v-icon>
      <h3 class="text-grey-lighten-1 mt-4">Выберите сервис из меню</h3>
    </v-container>
  </div>
</template>

<script>
import { defineAsyncComponent, inject } from 'vue'

// Статический реестр всех доступных federation компонентов
const FEDERATION_REGISTRY = {
  // Файловое хранилище
  'filestorage': {
    loader: () => import('filestorage/App'),
    name: 'FileStorage',
    props: ['apiClient', 'userId', 'permissions'],
    meta: {
      title: 'Файловое хранилище',
      description: 'Управление файлами и документами'
    }
  },
}

export default {
  name: 'FederationLoader',
  
  props: {
    // Дополнительные пропсы для передачи в компонент
    componentProps: {
      type: Object,
      default: () => ({})
    }
  },
  
  setup() {
    // Получаем API клиент через inject
    const apiClient = inject('apiClient', null)
    return { apiClient }
  },
  
  data() {
    return {
      currentComponent: null,
      loading: false,
      error: null,
      loadedComponents: new Map(),
      serviceName: null
    }
  },
  
  computed: {
    serviceFromRoute() {
      return this.$route.params.service || this.$route.query.service
    },
    
    currentServiceMeta() {
      if (!this.serviceName) return null
      return FEDERATION_REGISTRY[this.serviceName]?.meta
    }
  },
  
  watch: {
    serviceFromRoute: {
      handler(newService) {
        if (newService !== this.serviceName) {
          this.loadService(newService)
        }
      },
      immediate: true
    }
  },
  
  methods: {
    async loadService(serviceName) {
      if (!serviceName) {
        this.currentComponent = null
        this.serviceName = null
        this.error = null
        return
      }
      
      // Проверяем API клиент
      if (!this.apiClient) {
        this.error = { message: 'API клиент недоступен. Проверьте подключение к host приложению.' }
        return
      }
      
      const serviceConfig = FEDERATION_REGISTRY[serviceName]
      if (!serviceConfig) {
        this.error = { message: `Сервис "${serviceName}" не найден в реестре` }
        this.serviceName = serviceName
        return
      }
      
      if (this.loadedComponents.has(serviceName)) {
        this.currentComponent = this.loadedComponents.get(serviceName)
        this.serviceName = serviceName
        this.error = null
        return
      }
      
      this.loading = true
      this.error = null
      this.serviceName = serviceName
      
      try {
        console.log(`[FederationLoader] Загружаем сервис: ${serviceName}`)
        
        const asyncComponent = defineAsyncComponent({
          loader: serviceConfig.loader,
          delay: 200,
          timeout: 10000,
          errorComponent: {
            template: `
              <v-alert type="error" variant="tonal">
                <v-alert-title>Ошибка загрузки компонента</v-alert-title>
                <div>Не удалось загрузить сервис "${serviceName}"</div>
              </v-alert>
            `
          },
          loadingComponent: {
            template: '<v-skeleton-loader type="article"></v-skeleton-loader>'
          }
        })
        
        this.loadedComponents.set(serviceName, asyncComponent)
        this.currentComponent = asyncComponent
        
        this.$emit('service-loaded', {
          serviceName,
          meta: serviceConfig.meta
        })
        
        console.log(`[FederationLoader] Сервис ${serviceName} загружен успешно`)
        
      } catch (error) {
        console.error(`[FederationLoader] Ошибка загрузки ${serviceName}:`, error)
        this.error = {
          message: `Не удалось загрузить сервис: ${error.message}`
        }
        
        this.$emit('service-error', {
          serviceName,
          error
        })
      } finally {
        this.loading = false
      }
    },
    
    retryLoad() {
      if (this.serviceName) {
        this.loadedComponents.delete(this.serviceName)
        this.loadService(this.serviceName)
      }
    },
    
    handleServiceEvent(event) {
      console.log(`[FederationLoader] Событие от сервиса ${this.serviceName}:`, event)
      
      this.$emit('service-event', {
        service: this.serviceName,
        ...event
      })
    },
    
    getServiceMeta(serviceName) {
      return FEDERATION_REGISTRY[serviceName]?.meta
    },
    
    getAvailableServices() {
      return Object.keys(FEDERATION_REGISTRY).map(key => ({
        key,
        ...FEDERATION_REGISTRY[key].meta
      }))
    }
  }
}
</script>