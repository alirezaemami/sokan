/** Sign-in and sign-up screens bounce visitors who are already signed in. */
export default defineNuxtRouteMiddleware(async () => {
  if (import.meta.server) return
  const { ensure, homePath } = useAuth()
  const me = await ensure()
  if (me?.user) return navigateTo(homePath.value)
})
