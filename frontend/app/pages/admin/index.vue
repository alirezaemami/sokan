<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'admin' })
const { t } = useI18n()
useHead({ title: t('admin.nav.overview') })
const api = useSokan()
const fmt = useFormat()
const countryLabel = useCountryLabel()

const { data, status } = await useAsyncData('admin-overview', () => api.admin.overview(), { server: false })
const k = computed(() => data.value?.kpis)
const cur = computed(() => data.value?.currency || 'USD')

const revenueChange = computed(() => {
  if (!k.value?.revenue_last_month) return null
  return Math.round(((k.value.revenue_month - k.value.revenue_last_month) / k.value.revenue_last_month) * 100)
})

const attention = computed(() => {
  const a = data.value?.attention
  if (!a) return []
  return [
    { key: 'forwarders', icon: 'building', count: a.forwarders, to: '/admin/forwarders?status=Pending' },
    { key: 'topups', icon: 'credit-card', count: a.topups, to: '/admin/topups', extra: a.topups ? fmt.money(a.topups_amount, cur.value) : '' },
    { key: 'reviews', icon: 'star', count: a.reviews, to: '/admin/reviews' },
    { key: 'messages', icon: 'mail', count: a.messages, to: '/admin/messages' },
  ]
})

const day = (d: string) => fmt.date(d, 'short')
const activity = computed(() => (data.value?.series || []).map((s) => ({ label: day(s.date), values: [s.requests, s.quotes] })))
const revenue = computed(() => (data.value?.series || []).map((s) => ({ label: day(s.date), values: [s.revenue] })))
</script>

<template>
  <div>
    <PortalHeading :title="$t('admin.overview.title')" :subtitle="$t('admin.overview.subtitle')">
      <AppButton to="/admin/reports" variant="secondary" icon="chart">{{ $t('admin.nav.reports') }}</AppButton>
    </PortalHeading>

    <div v-if="status === 'pending' && !data" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><div v-for="i in 8" :key="i" class="skeleton h-32" /></div>
    <template v-else-if="data && k">
      <!-- Work waiting -->
      <section :aria-label="$t('admin.overview.attention')">
        <h2 class="chart-label mb-3 text-faint">{{ $t('admin.overview.attention') }}</h2>
        <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <NuxtLinkLocale
            v-for="a in attention"
            :key="a.key"
            :to="a.to"
            class="group flex items-center gap-3 rounded-2xl border p-4 transition-colors"
            :class="a.count ? 'border-buoy/30 bg-buoy/8 hover:border-buoy/60' : 'border-line bg-surface hover:border-line-strong'"
          >
            <span class="grid size-10 shrink-0 place-items-center rounded-xl" :class="a.count ? 'bg-buoy text-white' : 'bg-sunken text-faint'"><AppIcon :name="a.icon" :size="18" /></span>
            <div class="min-w-0">
              <p class="font-display text-2xl leading-none tabular-nums">{{ fmt.number(a.count) }}</p>
              <p class="mt-1 truncate text-xs text-muted">{{ $t(`admin.overview.waiting.${a.key}`) }}<template v-if="a.extra"> · {{ a.extra }}</template></p>
            </div>
          </NuxtLinkLocale>
        </div>
      </section>

      <!-- KPIs -->
      <div class="mt-6 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <div class="relative col-span-2 overflow-hidden rounded-2xl bg-night-900 p-5 text-white lg:col-span-1 dark:ring-1 dark:ring-tide/20">
          <p class="text-sm text-white/70">{{ $t('admin.overview.revenueMonth') }}</p>
          <p class="font-display mt-2 text-4xl tabular-nums">{{ fmt.money(k.revenue_month, cur) }}</p>
          <p v-if="revenueChange !== null" class="mt-2 text-xs" :class="revenueChange >= 0 ? 'text-tide' : 'text-buoy'">
            {{ revenueChange >= 0 ? '▲' : '▼' }} {{ $t('admin.overview.vsLastMonth', { n: fmt.number(Math.abs(revenueChange)) }) }}
          </p>
          <p class="mt-1 text-xs text-white/55">{{ $t('admin.overview.revenueTotal', { amount: fmt.money(k.revenue_total, cur) }) }}</p>
        </div>
        <StatTile icon="building" :label="$t('admin.overview.forwarders')" :value="fmt.number(k.forwarders_active)" :hint="$t('admin.overview.ofTotal', { n: fmt.number(k.forwarders_total) })" />
        <StatTile icon="list-checks" tone="buoy" :label="$t('admin.overview.openRequests')" :value="fmt.number(k.requests_open)" :hint="$t('admin.overview.booked', { n: fmt.number(k.requests_booked) })" />
        <StatTile icon="wallet" tone="tide" class="col-span-2 sm:col-span-1" :label="$t('admin.overview.walletFloat')" :value="fmt.money(k.wallet_float, cur)" :hint="$t('admin.overview.walletFloatHint')" />
      </div>
      <div class="mt-3 grid grid-cols-3 gap-3 sm:mt-4 sm:gap-4">
        <div class="card p-4"><p class="font-display text-2xl tabular-nums">{{ fmt.number(k.customers) }}</p><p class="text-xs text-muted">{{ $t('admin.overview.customers') }}</p></div>
        <div class="card p-4"><p class="font-display text-2xl tabular-nums">{{ fmt.number(k.requests_total) }}</p><p class="text-xs text-muted">{{ $t('admin.overview.requestsTotal') }}</p></div>
        <div class="card p-4"><p class="font-display text-2xl tabular-nums">{{ fmt.number(k.quotes) }}</p><p class="text-xs text-muted">{{ $t('admin.overview.quotes') }}</p></div>
      </div>

      <!-- Last 30 days -->
      <div class="mt-6 grid gap-4 lg:grid-cols-2">
        <section class="card p-5">
          <h2 class="font-semibold">{{ $t('admin.overview.activity') }}</h2>
          <p class="mb-4 text-xs text-faint">{{ $t('admin.overview.last30') }}</p>
          <BarChart :data="activity" :series="[$t('admin.overview.requests'), $t('admin.overview.quotes')]" :label-every="7" />
        </section>
        <section class="card p-5">
          <h2 class="font-semibold">{{ $t('admin.overview.revenue') }}</h2>
          <p class="mb-4 text-xs text-faint">{{ $t('admin.overview.revenueHint') }}</p>
          <BarChart :data="revenue" :series="[$t('admin.overview.revenue')]" :format="(v) => fmt.money(v, cur, 0)" :label-every="7" />
        </section>
      </div>

      <div class="mt-6 grid gap-4 lg:grid-cols-5">
        <section class="card overflow-hidden p-0 lg:col-span-3">
          <div class="flex items-center justify-between border-b border-line px-5 py-4">
            <h2 class="font-semibold">{{ $t('admin.overview.recentRequests') }}</h2>
            <NuxtLinkLocale to="/admin/requests" class="text-sm font-semibold text-sea hover:underline">{{ $t('common.viewAll') }}</NuxtLinkLocale>
          </div>
          <ul v-if="data.recent_requests.length" class="divide-y divide-line">
            <li v-for="r in data.recent_requests" :key="r.name">
              <NuxtLinkLocale :to="`/admin/requests/${r.name}`" class="flex items-center gap-3 px-5 py-3 hover:bg-sunken/60">
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-semibold">{{ r.title }}</p>
                  <p class="truncate text-xs text-faint">{{ r.name }} · {{ r.customer_name }} · {{ fmt.relative(r.creation) }}</p>
                </div>
                <span class="hidden text-xs text-muted tabular-nums sm:block">{{ $t('admin.requests.quotesN', { n: r.quote_count }) }}</span>
                <StatusPill :status="r.status" />
              </NuxtLinkLocale>
            </li>
          </ul>
          <EmptyState v-else icon="inbox" :title="$t('admin.requests.empty')" />
        </section>
        <section class="card overflow-hidden p-0 lg:col-span-2">
          <div class="flex items-center justify-between border-b border-line px-5 py-4">
            <h2 class="font-semibold">{{ $t('admin.overview.awaitingApproval') }}</h2>
            <NuxtLinkLocale to="/admin/forwarders?status=Pending" class="text-sm font-semibold text-sea hover:underline">{{ $t('common.viewAll') }}</NuxtLinkLocale>
          </div>
          <ul v-if="data.pending_forwarders.length" class="divide-y divide-line">
            <li v-for="f in data.pending_forwarders" :key="f.name">
              <NuxtLinkLocale :to="`/admin/forwarders/${f.name}`" class="flex items-center gap-3 px-5 py-3 hover:bg-sunken/60">
                <CompanyAvatar :name="f.company_name" :logo="f.logo" size="sm" />
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-semibold">{{ f.company_name }}</p>
                  <p class="truncate text-xs text-faint">{{ [f.city, countryLabel(f.country)].filter(Boolean).join(', ') }} · {{ fmt.relative(f.creation) }}</p>
                </div>
                <AppIcon name="chevron-right" :size="16" class="text-faint" flip />
              </NuxtLinkLocale>
            </li>
          </ul>
          <EmptyState v-else icon="circle-check" :title="$t('admin.overview.noneWaiting')" />
        </section>
      </div>
    </template>
  </div>
</template>
