import { createRouter, createWebHistory } from 'vue-router';
import index from '../pages/index.vue';
import about from '../pages/about.vue';
import FederationLoader from '../components/FederationLoader.vue';

const routes = [
  { path: '/', component: index },
  { path: '/about', component: about },
  { path: '/service/:service', component: FederationLoader },
];

const router = createRouter({
  history: createWebHistory(),
  routes: routes
})

export default router
