import axios from 'axios'

export function createAuthenticatedAxios(keycloakInstance) {
  const apiClient = axios.create({
    baseURL: process.env.VITE_API_BASE_URL,
    timeout: 10000
  })

  apiClient.interceptors.request.use(
    async (config) => {
      if (keycloakInstance.authenticated) {
        if (keycloakInstance.tokenParsed.exp * 1000 - Date.now() < 30000) {
          try {
            await keycloakInstance.updateToken(30)
            console.log('Token refreshed successfully')
          } catch (error) {
            console.error('Token refresh failed:', error)
            keycloakInstance.login()
            return Promise.reject(error)
          }
        }
        
        config.headers.Authorization = `Bearer ${keycloakInstance.token}`
      }
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response?.status === 401) {
        try {
          await keycloakInstance.updateToken(-1)
          const originalRequest = error.config
          originalRequest.headers.Authorization = `Bearer ${keycloakInstance.token}`
          return apiClient(originalRequest)
        } catch (refreshError) {
          console.error('Token refresh failed on 401:', refreshError)
          keycloakInstance.login()
          return Promise.reject(refreshError)
        }
      }
      return Promise.reject(error)
    }
  )

  return apiClient
}