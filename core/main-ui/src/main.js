import { createApp } from 'vue'
import App from './App.vue'
import { registerPlugins } from './plugins'
import { createAuthenticatedAxios } from './services/api'
import { setApiClient } from './services/apiClientExport'
import VueKeycloakJs from '@dsb-norge/vue-keycloak-js'

const app = createApp(App);

const initApp = (keycloak) => {
  registerPlugins(app);
  const apiClient = createAuthenticatedAxios(keycloak);
  setApiClient(apiClient);
  app.config.globalProperties.$api = apiClient;
  app.provide('apiClient', apiClient);
  app.mount('#app');
}

app.use(VueKeycloakJs, {
  init: {
    onLoad: 'check-sso',
    silentCheckSsoRedirectUri: `${window.location.origin}/silent-check-sso.html`,
    pkceMethod: 'S256',
    checkLoginIframe: true
  },
  config: {
    url: `${window.location.origin}${import.meta.env.VITE_KEYCLOAK_URL}`,
    realm: import.meta.env.VITE_KEYCLOAK_REALM,
    clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID
  },
  onReady: (keycloak) => initApp(keycloak)
});
