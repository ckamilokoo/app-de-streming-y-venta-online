export default defineNuxtConfig({
  // SPA: evita bugs de hidratación con WebRTC (decisión del plan, sección 7)
  ssr: false,
  devtools: { enabled: true },
  css: ['~/assets/main.css'],
  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8000',
    },
  },
})
