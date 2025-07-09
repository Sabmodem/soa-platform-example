import { createApp } from 'vue'
import axios from 'axios'
import FederationWrapper from './federation-wrapper.js'

const mockApiClient = axios.create({
  baseURL: '/',
  timeout: 10000
})

mockApiClient.interceptors.request.use(config => {
  config.headers.Authorization = 'Bearer mock-token-for-development'
  return config
})

const app = createApp(FederationWrapper, {
  apiClient: mockApiClient
})

app.mount('#app')
