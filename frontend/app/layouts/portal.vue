<script setup lang="ts">
/**
 * Shell for the three portals: customer (/account), forwarder (/partner)
 * and manager (/admin). The section is read from the URL; a user with more
 * than one profile can switch.
 */
const route = useRoute()
const { me, logout, isCustomer, isForwarder, isAdmin } = useAuth()
const fmt = useFormat()
const localePath = useLocalePath()

type Item = { to: string; icon: string; key: string; exact?: boolean; badge?: number }

const section = computed<'admin' | 'partner' | 'account'>(() =>
  /\/admin(\/|$)/.test(route.path) ? 'admin' : /\/partner(\/|$)/.test(route.path) ? 'partner' : 'account',
)
const isPartner = computed(() => section.value === 'partner')

const { counts, refresh: refreshCounts } = useAdminAttention()
watch(
  () => section.value === 'admin' && route.path,
  (on) => on && refreshCounts(),
  { immediate: true },
)

const nav = computed<Item[]>(() => {
  if (section.value === 'admin') {
    const c = counts.value
    return [
      { to: '/admin', icon: 'dashboard', key: 'admin.nav.overview', exact: true },
      { to: '/admin/forwarders', icon: 'building', key: 'admin.nav.forwarders', badge: c?.forwarders },
      { to: '/admin/requests', icon: 'list-checks', key: 'admin.nav.requests' },
      { to: '/admin/topups', icon: 'credit-card', key: 'admin.nav.topups', badge: c?.topups },
      { to: '/admin/customers', icon: 'users', key: 'admin.nav.customers' },
      { to: '/admin/reviews', icon: 'star', key: 'admin.nav.reviews', badge: c?.reviews },
      { to: '/admin/messages', icon: 'mail', key: 'admin.nav.messages', badge: c?.messages },
      { to: '/admin/finance', icon: 'receipt', key: 'admin.nav.finance' },
      { to: '/admin/reports', icon: 'chart', key: 'admin.nav.reports' },
      { to: '/admin/settings', icon: 'settings', key: 'admin.nav.settings' },
    ]
  }
  if (section.value === 'partner') {
    return [
      { to: '/partner', icon: 'dashboard', key: 'portal.nav.overview', exact: true },
      { to: '/partner/leads', icon: 'inbox', key: 'portal.nav.leads' },
      { to: '/partner/quotes', icon: 'receipt', key: 'portal.nav.quotes' },
      { to: '/partner/wallet', icon: 'wallet', key: 'portal.nav.wallet' },
      { to: '/partner/profile', icon: 'building', key: 'portal.nav.company' },
    ]
  }
  return [
    { to: '/account', icon: 'dashboard', key: 'portal.nav.overview', exact: true },
    { to: '/account/requests', icon: 'list-checks', key: 'portal.nav.requests' },
    { to: '/get-quote', icon: 'plus', key: 'portal.nav.newRequest' },
    { to: '/account/profile', icon: 'user', key: 'portal.nav.profile' },
  ]
})

// Phones get five slots at most; the rest live behind "More".
const TAB_LIMIT = 5
const tabs = computed(() => (nav.value.length > TAB_LIMIT ? nav.value.slice(0, TAB_LIMIT - 1) : nav.value))
const overflow = computed(() => (nav.value.length > TAB_LIMIT ? nav.value.slice(TAB_LIMIT - 1) : []))
const moreOpen = ref(false)
const moreBadge = computed(() => overflow.value.reduce((n, i) => n + (i.badge || 0), 0))
watch(() => route.fullPath, () => (moreOpen.value = false))

// Switcher between the portals this user can use.
const switches = computed(() =>
  [
    isAdmin.value && { to: '/admin', key: 'admin.as', on: section.value === 'admin' },
    isForwarder.value && { to: '/partner', key: 'portal.asForwarder', on: section.value === 'partner' },
    isCustomer.value && { to: '/account', key: 'portal.asShipper', on: section.value === 'account' },
  ].filter(Boolean) as { to: string; key: string; on: boolean }[],
)

function isActive(item: { to: string; exact?: boolean }) {
  const p = localePath(item.to)
  return item.exact ? route.path === p : route.path.startsWith(p)
}
</script>

<template>
  <div class="min-h-dvh bg-bg">
    <!-- Sidebar (desktop) -->
    <aside class="fixed inset-y-0 start-0 z-30 hidden w-68 flex-col border-e border-line bg-surface lg:flex">
      <div class="flex h-18 shrink-0 items-center gap-3 px-6">
        <NuxtLinkLocale to="/"><AppLogo /></NuxtLinkLocale>
        <span v-if="section === 'admin'" class="chart-label rounded-full bg-buoy/12 px-2 py-0.5 text-buoy">{{ $t('admin.badge') }}</span>
      </div>
      <div v-if="switches.length > 1" class="px-4">
        <div class="grid gap-1 rounded-2xl bg-sunken p-1.5 text-xs font-semibold" :style="{ gridTemplateColumns: `repeat(${switches.length}, minmax(0, 1fr))` }">
          <NuxtLinkLocale
            v-for="s in switches"
            :key="s.to"
            :to="s.to"
            class="truncate rounded-xl px-2 py-2 text-center"
            :class="s.on ? 'bg-surface text-ink shadow-sm' : 'text-muted hover:text-ink'"
          >
            {{ $t(s.key) }}
          </NuxtLinkLocale>
        </div>
      </div>
      <nav class="no-scrollbar mt-4 flex flex-1 flex-col gap-1 overflow-y-auto px-4 pb-4">
        <NuxtLinkLocale
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="group flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-[0.94rem] font-semibold transition-colors"
          :class="isActive(item) ? 'bg-sea/10 text-sea' : 'text-ink-soft hover:bg-sunken hover:text-ink'"
        >
          <AppIcon :name="item.icon" :size="19" class="shrink-0 transition-transform group-hover:scale-110" />
          <span class="min-w-0 flex-1 truncate">{{ $t(item.key) }}</span>
          <span v-if="item.badge" class="min-w-6 rounded-full bg-buoy px-1.5 text-center text-xs font-bold leading-5 text-white tabular-nums">{{ item.badge }}</span>
        </NuxtLinkLocale>
      </nav>

      <div v-if="isPartner && me?.forwarder" class="mx-4 mb-4 overflow-hidden rounded-2xl bg-night-900 p-4 text-white">
        <p class="text-xs font-medium text-white/75">{{ $t('portal.walletBalance') }}</p>
        <p class="font-display mt-1 text-3xl tabular-nums">{{ fmt.money(me.forwarder.wallet_balance, me.forwarder.wallet_currency) }}</p>
        <NuxtLinkLocale to="/partner/wallet" class="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-white/90 hover:text-white">
          {{ $t('portal.topUp') }} <AppIcon name="arrow-right" :size="14" flip />
        </NuxtLinkLocale>
      </div>

      <div class="flex shrink-0 items-center gap-3 border-t border-line p-4">
        <span class="grid size-10 place-items-center rounded-full bg-sea/10 font-bold text-sea">{{ (me?.full_name || '?').charAt(0) }}</span>
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-semibold">{{ me?.full_name }}</p>
          <p class="truncate text-xs text-faint">{{ me?.user }}</p>
        </div>
        <button type="button" class="rounded-lg p-2 text-faint hover:bg-sunken hover:text-danger" :aria-label="$t('nav.logout')" @click="logout">
          <AppIcon name="log-out" :size="18" flip />
        </button>
      </div>
    </aside>

    <!-- Top bar -->
    <header class="glass sticky top-0 z-20 border-x-0 border-t-0 lg:ms-68">
      <div class="flex h-16 items-center gap-3 px-4 sm:px-6 lg:h-18 lg:px-8">
        <NuxtLinkLocale to="/" class="lg:hidden"><AppLogo compact /></NuxtLinkLocale>
        <div class="min-w-0 flex-1">
          <p v-if="section === 'admin'" class="truncate text-sm font-bold lg:text-base">{{ $t('admin.title') }}</p>
          <p v-else-if="isPartner && me?.forwarder" class="truncate text-sm font-bold lg:text-base">{{ me.forwarder.company_name }}</p>
          <p v-else class="truncate text-sm font-bold lg:text-base">{{ $t('portal.hello', { name: me?.full_name?.split(' ')[0] || '' }) }}</p>
        </div>
        <NuxtLinkLocale
          v-if="isPartner && me?.forwarder"
          to="/partner/wallet"
          class="inline-flex items-center gap-2 rounded-xl bg-sunken px-3 py-2 text-sm font-bold tabular-nums lg:hidden"
        >
          <AppIcon name="wallet" :size="16" class="text-sea" />
          {{ fmt.money(me.forwarder.wallet_balance, me.forwarder.wallet_currency) }}
        </NuxtLinkLocale>
        <div class="hidden sm:block"><LangSwitch /></div>
        <ThemeToggle />
        <button type="button" class="grid size-10 place-items-center rounded-xl text-ink-soft hover:bg-sunken lg:hidden" :aria-label="$t('nav.logout')" @click="logout">
          <AppIcon name="log-out" :size="19" flip />
        </button>
      </div>
    </header>

    <main class="px-4 pt-6 pb-28 sm:px-6 lg:ms-68 lg:px-8 lg:pt-8 lg:pb-12">
      <div class="mx-auto max-w-6xl">
        <slot />
      </div>
    </main>

    <!-- Bottom tabs (mobile) -->
    <nav class="glass fixed inset-x-0 bottom-0 z-30 border-x-0 border-b-0 safe-bottom lg:hidden">
      <div class="mx-auto grid max-w-lg" :style="{ gridTemplateColumns: `repeat(${tabs.length + (overflow.length ? 1 : 0)}, minmax(0, 1fr))` }">
        <NuxtLinkLocale
          v-for="item in tabs"
          :key="item.to"
          :to="item.to"
          class="flex min-w-0 flex-col items-center gap-1 pt-2.5 pb-1 text-[0.68rem] font-semibold transition-colors"
          :class="isActive(item) ? 'text-sea' : 'text-faint'"
        >
          <span class="relative grid h-7 w-12 place-items-center rounded-full transition-all" :class="isActive(item) && 'bg-sea/12'">
            <AppIcon :name="item.icon" :size="20" />
            <span v-if="item.badge" class="absolute -top-1 end-1 min-w-4 rounded-full bg-buoy px-1 text-center text-[0.6rem] font-bold leading-4 text-white">{{ item.badge }}</span>
          </span>
          <span class="max-w-full truncate px-1">{{ $t(item.key) }}</span>
        </NuxtLinkLocale>
        <button
          v-if="overflow.length"
          type="button"
          class="flex min-w-0 flex-col items-center gap-1 pt-2.5 pb-1 text-[0.68rem] font-semibold transition-colors"
          :class="overflow.some(isActive) ? 'text-sea' : 'text-faint'"
          :aria-expanded="moreOpen"
          @click="moreOpen = true"
        >
          <span class="relative grid h-7 w-12 place-items-center rounded-full" :class="overflow.some(isActive) && 'bg-sea/12'">
            <AppIcon name="menu" :size="20" />
            <span v-if="moreBadge" class="absolute -top-1 end-1 min-w-4 rounded-full bg-buoy px-1 text-center text-[0.6rem] font-bold leading-4 text-white">{{ moreBadge }}</span>
          </span>
          {{ $t('admin.nav.more') }}
        </button>
      </div>
    </nav>

    <AppModal v-model="moreOpen" :title="$t('admin.nav.more')" size="sm">
      <div class="grid grid-cols-2 gap-2">
        <NuxtLinkLocale
          v-for="item in overflow"
          :key="item.to"
          :to="item.to"
          class="relative flex items-center gap-3 rounded-2xl p-4 text-sm font-semibold"
          :class="isActive(item) ? 'bg-sea/10 text-sea' : 'bg-sunken text-ink-soft'"
        >
          <AppIcon :name="item.icon" :size="19" class="shrink-0" />
          <span class="min-w-0 flex-1 truncate">{{ $t(item.key) }}</span>
          <span v-if="item.badge" class="rounded-full bg-buoy px-1.5 text-xs font-bold leading-5 text-white">{{ item.badge }}</span>
        </NuxtLinkLocale>
      </div>
      <div v-if="switches.length > 1" class="mt-4 flex flex-wrap gap-2 border-t border-line pt-4">
        <AppButton v-for="s in switches.filter((x) => !x.on)" :key="s.to" :to="s.to" variant="secondary" size="sm">{{ $t(s.key) }}</AppButton>
      </div>
    </AppModal>
  </div>
</template>
