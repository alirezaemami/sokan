<script setup lang="ts">
/**
 * Shell for both portals. The section (customer /account or forwarder
 * /partner) is read from the URL; a user with both profiles can switch.
 */
const route = useRoute()
const { me, logout, isCustomer, isForwarder } = useAuth()
const fmt = useFormat()

const isPartner = computed(() => /\/partner(\/|$)/.test(route.path))

const nav = computed(() =>
  isPartner.value
    ? [
        { to: '/partner', icon: 'dashboard', key: 'portal.nav.overview', exact: true },
        { to: '/partner/leads', icon: 'inbox', key: 'portal.nav.leads' },
        { to: '/partner/quotes', icon: 'receipt', key: 'portal.nav.quotes' },
        { to: '/partner/wallet', icon: 'wallet', key: 'portal.nav.wallet' },
        { to: '/partner/profile', icon: 'building', key: 'portal.nav.company' },
      ]
    : [
        { to: '/account', icon: 'dashboard', key: 'portal.nav.overview', exact: true },
        { to: '/account/requests', icon: 'list-checks', key: 'portal.nav.requests' },
        { to: '/get-quote', icon: 'plus', key: 'portal.nav.newRequest' },
        { to: '/account/profile', icon: 'user', key: 'portal.nav.profile' },
      ],
)

const localePath = useLocalePath()
function isActive(item: { to: string; exact?: boolean }) {
  const p = localePath(item.to)
  return item.exact ? route.path === p : route.path.startsWith(p)
}
</script>

<template>
  <div class="min-h-dvh bg-bg">
    <!-- Sidebar (desktop) -->
    <aside class="fixed inset-y-0 start-0 z-30 hidden w-68 flex-col border-e border-line bg-surface lg:flex">
      <div class="flex h-18 items-center px-6">
        <NuxtLinkLocale to="/"><AppLogo /></NuxtLinkLocale>
      </div>
      <div class="px-4">
        <div class="rounded-2xl bg-sunken p-1.5" v-if="isCustomer && isForwarder">
          <div class="grid grid-cols-2 gap-1 text-xs font-semibold">
            <NuxtLinkLocale to="/partner" class="rounded-xl px-3 py-2 text-center" :class="isPartner ? 'bg-surface text-ink shadow-sm' : 'text-muted'">{{ $t('portal.asForwarder') }}</NuxtLinkLocale>
            <NuxtLinkLocale to="/account" class="rounded-xl px-3 py-2 text-center" :class="!isPartner ? 'bg-surface text-ink shadow-sm' : 'text-muted'">{{ $t('portal.asShipper') }}</NuxtLinkLocale>
          </div>
        </div>
      </div>
      <nav class="mt-4 flex flex-1 flex-col gap-1 px-4">
        <NuxtLinkLocale
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="group flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-[0.94rem] font-semibold transition-all"
          :class="isActive(item) ? 'bg-brand/10 text-brand dark:text-brand-soft' : 'text-ink-soft hover:bg-sunken hover:text-ink'"
        >
          <AppIcon :name="item.icon" :size="19" class="transition-transform group-hover:scale-110" />
          {{ $t(item.key) }}
        </NuxtLinkLocale>
      </nav>

      <div v-if="isPartner && me?.forwarder" class="mx-4 mb-4 overflow-hidden rounded-2xl bg-brand-gradient p-4 text-white">
        <p class="text-xs font-medium text-white/75">{{ $t('portal.walletBalance') }}</p>
        <p class="mt-1 text-2xl font-extrabold tabular-nums">{{ fmt.money(me.forwarder.wallet_balance, me.forwarder.wallet_currency) }}</p>
        <NuxtLinkLocale to="/partner/wallet" class="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-white/90 hover:text-white">
          {{ $t('portal.topUp') }} <AppIcon name="arrow-right" :size="14" flip />
        </NuxtLinkLocale>
      </div>

      <div class="flex items-center gap-3 border-t border-line p-4">
        <span class="grid size-10 place-items-center rounded-full bg-brand/10 font-bold text-brand">{{ (me?.full_name || '?').charAt(0) }}</span>
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
          <p v-if="isPartner && me?.forwarder" class="truncate text-sm font-bold lg:text-base">{{ me.forwarder.company_name }}</p>
          <p v-else class="truncate text-sm font-bold lg:text-base">{{ $t('portal.hello', { name: me?.full_name?.split(' ')[0] || '' }) }}</p>
        </div>
        <NuxtLinkLocale
          v-if="isPartner && me?.forwarder"
          to="/partner/wallet"
          class="inline-flex items-center gap-2 rounded-xl bg-sunken px-3 py-2 text-sm font-bold tabular-nums lg:hidden"
        >
          <AppIcon name="wallet" :size="16" class="text-brand" />
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
      <div class="mx-auto grid max-w-lg" :style="{ gridTemplateColumns: `repeat(${nav.length}, minmax(0, 1fr))` }">
        <NuxtLinkLocale
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="flex flex-col items-center gap-1 pt-2.5 pb-1 text-[0.68rem] font-semibold transition-colors"
          :class="isActive(item) ? 'text-brand' : 'text-faint'"
        >
          <span class="grid h-7 w-12 place-items-center rounded-full transition-all" :class="isActive(item) && 'bg-brand/12'">
            <AppIcon :name="item.icon" :size="20" />
          </span>
          {{ $t(item.key) }}
        </NuxtLinkLocale>
      </div>
    </nav>
  </div>
</template>
