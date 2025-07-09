import Components from 'unplugin-vue-components/vite'
import Vue from '@vitejs/plugin-vue'
import Vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'
import ViteFonts from 'unplugin-fonts/vite'
import VueRouter from 'unplugin-vue-router/vite'
import federation from '@originjs/vite-plugin-federation';
import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'
const hash = Math.floor(Math.random() * Date.now());
export default defineConfig({
  base: '/',
  plugins: [
    VueRouter(),
    Vue({
      template: { transformAssetUrls }
    }),
    federation({
      name: 'main-ui',
      filename: 'remoteEntry.js',
      remotes: {
        filestorage: '/ui/filestorage/assets/remoteEntry.js'
      },
      exposes: {
        './ApiClient': './src/services/apiClientExport.js',
      },
      shared: {
        vue: {
          singleton: true,
        },
        vuetify: {
          singleton: true,
        },
        axios: {
          singleton: true,
        },
      },
    }),
    Vuetify({
      autoImport: true,
      styles: {
        configFile: 'src/styles/settings.scss',
      },
    }),
    Components(),
    ViteFonts({
      google: {
        families: [{
          name: 'Roboto',
          styles: 'wght@100;300;400;500;700;900',
        }],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
    extensions: [
      '.js',
      '.json',
      '.jsx',
      '.mjs',
      '.ts',
      '.tsx',
      '.vue',
    ],
  },
  server: {
    port: 3000,
  }, 
  build: {
    target: 'esnext',
    outDir: 'dist',
    assetsDir: 'assets',
    minify: false,
    cssCodeSplit: false,
    rollupOptions: {
      output: {
        entryFileNames: `[name]-${hash}.js`,
        chunkFileNames: `[name]-${hash}.js`,
        assetFileNames: `[name]-${hash}.[ext]`
      }
    }
  }  
});