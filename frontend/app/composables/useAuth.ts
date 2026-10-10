import type { Me } from '~/types/sokan'

/** The signed-in identity, shared app-wide. `null` = not loaded yet; `{ user: null }` = guest. */
export function useMe() {
  return useState<Me | null>('sokan-me', () => null)
}

export function useAuth() {
  const me = useMe()
  const api = useSokan()
  const localePath = useLocalePath()

  const isLoggedIn = computed(() => Boolean(me.value?.user))
  const isCustomer = computed(() => Boolean(me.value?.customer))
  const isForwarder = computed(() => Boolean(me.value?.forwarder))
  const isAdmin = computed(() => Boolean(me.value?.is_admin))

  /** Where a user belongs after signing in: managers, then forwarders (their workplace), then shippers. */
  const homePath = computed(() =>
    isAdmin.value
      ? localePath('/admin')
      : isForwarder.value
        ? localePath('/partner')
        : isCustomer.value
          ? localePath('/account')
          : localePath('/'),
  )

  async function refresh() {
    try {
      me.value = await api.me()
    } catch {
      me.value = { user: null }
    }
    return me.value
  }

  async function ensure() {
    if (me.value === null) await refresh()
    return me.value
  }

  async function login(email: string, password: string, captcha: string) {
    // A stale session would demand a CSRF token the login form doesn't have.
    me.value = { user: null }
    await api.login(email.trim().toLowerCase(), password, captcha)
    return refresh()
  }

  /** Signed in but the email isn't confirmed yet (managers are exempt). */
  const needsVerification = computed(() => Boolean(me.value?.user) && !me.value?.email_verified && !isAdmin.value)

  /** The code page, coming back to `next` (an already-localised path) afterwards. */
  function verifyPath(next?: string) {
    return { path: localePath('/verify-email'), query: next ? { redirect: next } : {} }
  }

  async function logout() {
    try {
      await api.logout()
    } finally {
      me.value = { user: null }
      await navigateTo(localePath('/'))
    }
  }

  function setMe(data: Me) {
    me.value = data
  }

  return {
    me,
    isLoggedIn,
    isCustomer,
    isForwarder,
    isAdmin,
    homePath,
    needsVerification,
    verifyPath,
    refresh,
    ensure,
    login,
    logout,
    setMe,
  }
}
