<template>
  <v-app>
    <v-app-bar>
      <template #prepend>
        <v-app-bar-nav-icon v-if="keycloak.authenticated" @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
      </template>
      <v-app-bar-title>UPE</v-app-bar-title>
      <template #append>
        <v-tabs>
          <v-tab to="/">Main</v-tab>
          <v-tab to="/about">About</v-tab>
          <v-tab v-if="!keycloak.authenticated" @click="keycloak.login()">Login</v-tab>
          <v-tab v-if="keycloak.authenticated" @click="keycloak.accountManagement()">Profile</v-tab>
        </v-tabs>
      </template>
    </v-app-bar>
    <v-navigation-drawer v-if="keycloak.authenticated" v-model="drawer">
      <v-list density="compact">
        <v-list-item v-for="role in keycloak.realmAccess.roles.filter(role => role.indexOf('module') !== -1).map(role => role.split('-')[1])" link :title="role" :to="`/service/${role}`"></v-list-item>
      </v-list>
    </v-navigation-drawer>
    <v-main>
      <RouterView />
    </v-main>
  </v-app>
</template>

<script setup>
import { useKeycloak } from '@dsb-norge/vue-keycloak-js'
const keycloak = useKeycloak();
</script>

<script>
export default {
  data() {
    return {
      drawer: false,
    }
  }
}
</script>