/**
 * Portal guard. Pages opt in with
 *   definePageMeta({ middleware: 'auth', role: 'customer' | 'forwarder' })
 *
 * Portals render client-only (see nuxt.config routeRules), so this always
 * runs in the browser where the Frappe session cookie is available.
 */
export default defineNuxtRouteMiddleware(async (to) => {
  if (import.meta.server) return
  const { ensure, isCustomer, isForwarder } = useAuth()
  const localePath = useLocalePath()
  const me = await ensure()

  if (!me?.user) {
    return navigateTo({ path: localePath('/login'), query: { redirect: to.fullPath } })
  }

  const role = to.meta.role as 'customer' | 'forwarder' | undefined
  if (role === 'forwarder' && !isForwarder.value) {
    return navigateTo(localePath(isCustomer.value ? '/account' : '/register/forwarder'))
  }
  if (role === 'customer' && !isCustomer.value) {
    // A forwarder may also ship goods; offer them a customer profile.
    return navigateTo({ path: localePath('/get-quote') })
  }
})
