export function useApi() {
  const config = useRuntimeConfig()
  const { token } = useAuth()

  const api = $fetch.create({
    baseURL: config.public.apiBase,
    onRequest({ options }) {
      if (token.value) {
        options.headers.set('Authorization', `Bearer ${token.value}`)
      }
    },
  })

  // imageUrl del API es relativo (/uploads/x.jpg) => prefijar apiBase
  const assetUrl = (path: string | null) =>
    path ? `${config.public.apiBase}${path}` : null

  return { api, assetUrl }
}
