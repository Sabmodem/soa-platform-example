// // Plugins
// import Components from 'unplugin-vue-components/vite'
// import Vue from '@vitejs/plugin-vue'
// import Vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'
// import ViteFonts from 'unplugin-fonts/vite'
// import federation from '@originjs/vite-plugin-federation'

// // Utilities
// import { defineConfig } from 'vite'
// import { fileURLToPath, URL } from 'node:url'

// // https://vitejs.dev/config/
// export default defineConfig({
//   plugins: [
//     Vue({
//       template: { transformAssetUrls }
//     }),
//     federation({
//       name: 'filestorage', // Уникальное имя вашего приложения
//       filename: 'filestorage.js',
//       // Экспортируемые модули
//       exposes: {
//         './App': './src/App.vue',
//         './bootstrap': './src/bootstrap.js'
//       },
//       // Общие зависимости
//       shared: {
//         vue: {
//           singleton: true,
//         },
//         vuetify: {
//           singleton: true
//         },
//       }
//     }),    
//     // https://github.com/vuetifyjs/vuetify-loader/tree/master/packages/vite-plugin#readme
//     Vuetify(),
//     Components(),
//     ViteFonts({
//       google: {
//         families: [{
//           name: 'Roboto',
//           styles: 'wght@100;300;400;500;700;900',
//         }],
//       },
//     }),
//   ],
//   define: { 'process.env': {} },
//   resolve: {
//     alias: {
//       '@': fileURLToPath(new URL('./src', import.meta.url))
//     },
//     extensions: [
//       '.js',
//       '.json',
//       '.jsx',
//       '.mjs',
//       '.ts',
//       '.tsx',
//       '.vue',
//     ],
//   },
//   server: {
//     port: 3000,
//   },
//   base: '/ui/filestorage/',
//   build: {
//     target: 'esnext',
//     minify: false,
//     cssCodeSplit: false
//   }
// })



import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import federation from '@originjs/vite-plugin-federation'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/ui/filestorage/', // или тот путь, по которому доступно ваше remote приложение
  plugins: [
    vue(),
    federation({
      name: 'filestorage',
      filename: 'remoteEntry.js',
      exposes: {
        './App': './src/federation-wrapper.js',
      },
      remotes: {
        'main-ui': '/assets/remoteEntry.js'
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
        // 'keycloak-js': {
        //   singleton: true,
        // }
      }
    }),
  ],
  build: {
    target: 'esnext',
    outDir: 'dist',
    assetsDir: 'assets', // Чаще всего чанки будут в dist/assets/
    minify: false, // Для простоты отладки
    cssCodeSplit: false, // Для простоты стилей
    rollupOptions: {
      external: [
        './src/main.js',
        '@/plugins',
        /^@\/plugins\/.*/
      ]
    }
  },
  // Это важно, чтобы Nginx мог проксировать!
})