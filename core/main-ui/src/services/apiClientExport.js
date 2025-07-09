let globalApiClient = null;
export function setApiClient(apiClient) {
  globalApiClient = apiClient;
}
export function getApiClient() {
  if (!globalApiClient) {
    throw new Error('API Client not initialized. Make sure host app is loaded first.');
  }
  return globalApiClient;
}
