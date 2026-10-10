<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'admin' })
const { t, locale } = useI18n()
useHead({ title: t('admin.nav.reports') })
const api = useSokan()
const fmt = useFormat()
const countryLabel = useCountryLabel()

const iso = (d: Date) => d.toISOString().slice(0, 10)
const daysAgo = (n: number) => iso(new Date(Date.now() - n * 864e5))
const PRESETS = [
  { key: '30', from: () => daysAgo(29) },
  { key: '90', from: () => daysAgo(89) },
  { key: '365', from: () => daysAgo(364) },
]
const preset = ref('90')
const range = reactive({ from_date: daysAgo(89), to_date: iso(new Date()) })
function choose(p: (typeof PRESETS)[number]) {
  preset.value = p.key
  range.from_date = p.from()
  range.to_date = iso(new Date())
}

const { data, status: loading } = await useAsyncData('admin-reports', () => api.admin.reports({ ...range }), { server: false, watch: [range] })
const cur = computed(() => data.value?.currency || 'USD')

const funnel = computed(() => {
  const f = data.value?.funnel
  if (!f) return []
  const top = Math.max(f.published, f.leads, 1)
  return (['published', 'leads', 'unlocks', 'quotes', 'booked'] as const).map((k) => ({ key: k, value: f[k], pct: (f[k] / top) * 100 }))
})
const monthLabel = (m: string) => new Intl.DateTimeFormat(locale.value, { month: 'short' }).format(new Date(`${m}-01T00:00:00`))
const money = computed(() => (data.value?.monthly || []).map((m) => ({ label: monthLabel(m.month), values: [m.revenue, m.topups] })))
const volume = computed(() => (data.value?.monthly || []).map((m) => ({ label: monthLabel(m.month), values: [m.requests, m.booked] })))
const revenueTotal = computed(() => {
  const r = data.value?.revenue
  return r ? r.unlocks + r.quotes + r.subscriptions : 0
})

function exportTable(kind: 'lanes' | 'modes' | 'forwarders') {
  const d = data.value
  if (!d) return
  const stamp = `${d.from_date}_${d.to_date}`
  if (kind === 'lanes')
    downloadCsv(`sokan-lanes-${stamp}.csv`, [
      { key: 'origin_country', label: t('admin.requests.origin') },
      { key: 'destination_country', label: t('admin.requests.destination') },
      { key: 'requests', label: t('admin.overview.requests') },
      { key: 'booked', label: t('admin.reports.booked') },
    ], d.lanes)
  else if (kind === 'modes')
    downloadCsv(`sokan-modes-${stamp}.csv`, [
      { key: 'mode', label: t('admin.requests.mode') },
      { key: 'requests', label: t('admin.overview.requests') },
      { key: 'booked', label: t('admin.reports.booked') },
    ], d.modes)
  else
    downloadCsv(`sokan-forwarders-${stamp}.csv`, [
      { key: 'company_name', label: t('admin.finance.forwarder') },
      { key: 'country', label: t('fields.country') },
      { key: 'unlocks', label: t('admin.forwarders.unlocked') },
      { key: 'quotes', label: t('admin.forwarders.quotes') },
      { key: 'won', label: t('admin.forwarders.won') },
      { key: 'fees', label: t('admin.reports.feesPaid') },
    ], d.top_forwarders)
}
</script>

<template>
  <div>
    <PortalHeading :title="$t('admin.nav.reports')" :subtitle="$t('admin.reports.subtitle')" />

    <div class="card mb-6 flex flex-wrap items-end gap-3 p-4">
      <div class="flex gap-1 rounded-xl bg-sunken p-1">
        <button v-for="p in PRESETS" :key="p.key" type="button" class="rounded-lg px-3 py-1.5 text-sm font-semibold" :class="preset === p.key ? 'bg-surface text-ink shadow-sm' : 'text-muted'" @click="choose(p)">
          {{ $t(`admin.reports.preset.${p.key}`) }}
        </button>
      </div>
      <FormField v-model="range.from_date" type="date" class="w-40" :label="$t('common.from')" @update:model-value="preset = ''" />
      <FormField v-model="range.to_date" type="date" class="w-40" :label="$t('common.to')" @update:model-value="preset = ''" />
    </div>

    <div v-if="loading === 'pending' && !data" class="grid gap-4 lg:grid-cols-2"><div v-for="i in 4" :key="i" class="skeleton h-72" /></div>
    <template v-else-if="data">
      <div class="grid gap-4 lg:grid-cols-2">
        <!-- Funnel -->
        <section class="card p-5">
          <h2 class="font-semibold">{{ $t('admin.reports.funnel') }}</h2>
          <p class="mb-4 text-xs text-faint">{{ $t('admin.reports.funnelHint') }}</p>
          <ol class="space-y-3">
            <li v-for="s in funnel" :key="s.key">
              <div class="mb-1 flex justify-between text-sm"><span>{{ $t(`admin.reports.stage.${s.key}`) }}</span><b class="tabular-nums">{{ fmt.number(s.value) }}</b></div>
              <div class="h-2.5 overflow-hidden rounded-full bg-sunken"><div class="h-full rounded-full bg-sea transition-[width] duration-700" :style="{ width: `${s.pct}%` }" /></div>
            </li>
          </ol>
          <div class="mt-5 grid grid-cols-3 gap-2 border-t border-line pt-4 text-center">
            <div><p class="font-display text-xl tabular-nums">{{ fmt.number(data.averages.leads_per_request, 1) }}</p><p class="text-xs text-muted">{{ $t('admin.reports.leadsPer') }}</p></div>
            <div><p class="font-display text-xl tabular-nums">{{ fmt.number(data.averages.quotes_per_request, 1) }}</p><p class="text-xs text-muted">{{ $t('admin.reports.quotesPer') }}</p></div>
            <div><p class="font-display text-xl tabular-nums">{{ fmt.number(data.averages.booking_rate, 1) }}%</p><p class="text-xs text-muted">{{ $t('admin.reports.bookingRate') }}</p></div>
          </div>
        </section>

        <!-- Revenue breakdown -->
        <section class="card p-5">
          <h2 class="font-semibold">{{ $t('admin.reports.revenue') }}</h2>
          <p class="font-display mt-2 text-4xl tabular-nums">{{ fmt.money(revenueTotal, cur) }}</p>
          <p class="text-xs text-faint">{{ $t('admin.reports.revenueHint') }}</p>
          <dl class="mt-5 divide-y divide-line text-sm">
            <div v-for="k in (['unlocks', 'quotes', 'subscriptions'] as const)" :key="k" class="flex justify-between py-2"><dt>{{ $t(`admin.reports.rev.${k}`) }}</dt><dd class="font-semibold tabular-nums">{{ fmt.money(data.revenue[k], cur) }}</dd></div>
            <div v-for="k in (['topups', 'bonuses', 'refunds', 'adjustments'] as const)" :key="k" class="flex justify-between py-2 text-muted"><dt>{{ $t(`admin.reports.rev.${k}`) }}</dt><dd class="tabular-nums">{{ fmt.money(data.revenue[k], cur) }}</dd></div>
          </dl>
        </section>

        <section class="card p-5">
          <h2 class="font-semibold">{{ $t('admin.reports.monthlyMoney') }}</h2>
          <p class="mb-4 text-xs text-faint">{{ $t('admin.reports.last12') }}</p>
          <BarChart :data="money" :series="[$t('admin.reports.rev.fees'), $t('admin.reports.rev.topups')]" :format="(v) => fmt.money(v, cur, 0)" :label-every="2" />
        </section>
        <section class="card p-5">
          <h2 class="font-semibold">{{ $t('admin.reports.monthlyVolume') }}</h2>
          <p class="mb-4 text-xs text-faint">{{ $t('admin.reports.last12') }}</p>
          <BarChart :data="volume" :series="[$t('admin.overview.requests'), $t('admin.reports.booked')]" :label-every="2" />
        </section>
      </div>

      <!-- Tables -->
      <div class="mt-4 grid gap-4 lg:grid-cols-2">
        <section class="card overflow-hidden p-0">
          <div class="flex items-center justify-between border-b border-line px-5 py-4">
            <h2 class="font-semibold">{{ $t('admin.reports.lanes') }}</h2>
            <button type="button" class="text-sm font-semibold text-sea hover:underline disabled:opacity-40" :disabled="!data.lanes.length" @click="exportTable('lanes')">{{ $t('admin.csv') }}</button>
          </div>
          <ul v-if="data.lanes.length" class="divide-y divide-line">
            <li v-for="l in data.lanes" :key="l.origin_country + l.destination_country" class="flex items-center gap-3 px-5 py-2.5 text-sm">
              <span class="min-w-0 flex-1 truncate">{{ countryLabel(l.origin_country, { flag: true }) }} → {{ countryLabel(l.destination_country, { flag: true }) }}</span>
              <span class="tabular-nums">{{ fmt.number(l.requests) }}</span>
              <span class="w-16 text-end text-xs text-muted tabular-nums">{{ $t('admin.reports.bookedN', { n: l.booked }) }}</span>
            </li>
          </ul>
          <EmptyState v-else icon="route" :title="$t('admin.reports.noData')" />
        </section>
        <section class="card overflow-hidden p-0">
          <div class="flex items-center justify-between border-b border-line px-5 py-4">
            <h2 class="font-semibold">{{ $t('admin.reports.modes') }}</h2>
            <button type="button" class="text-sm font-semibold text-sea hover:underline disabled:opacity-40" :disabled="!data.modes.length" @click="exportTable('modes')">{{ $t('admin.csv') }}</button>
          </div>
          <ul v-if="data.modes.length" class="divide-y divide-line">
            <li v-for="m in data.modes" :key="m.mode" class="flex items-center gap-3 px-5 py-2.5 text-sm">
              <span class="min-w-0 flex-1 truncate">{{ m.mode }}</span>
              <span class="tabular-nums">{{ fmt.number(m.requests) }}</span>
              <span class="w-16 text-end text-xs text-muted tabular-nums">{{ $t('admin.reports.bookedN', { n: m.booked }) }}</span>
            </li>
          </ul>
          <EmptyState v-else icon="layers" :title="$t('admin.reports.noData')" />
        </section>
      </div>

      <section class="card mt-4 overflow-hidden p-0">
        <div class="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 class="font-semibold">{{ $t('admin.reports.topForwarders') }}</h2>
          <button type="button" class="text-sm font-semibold text-sea hover:underline disabled:opacity-40" :disabled="!data.top_forwarders.length" @click="exportTable('forwarders')">{{ $t('admin.csv') }}</button>
        </div>
        <div v-if="data.top_forwarders.length" class="overflow-x-auto">
          <table class="w-full min-w-[560px] text-sm">
            <thead>
              <tr class="border-b border-line text-xs text-faint">
                <th class="px-5 py-3 text-start font-medium">{{ $t('admin.finance.forwarder') }}</th>
                <th class="px-3 py-3 text-end font-medium">{{ $t('admin.forwarders.unlocked') }}</th>
                <th class="px-3 py-3 text-end font-medium">{{ $t('admin.forwarders.quotes') }}</th>
                <th class="px-3 py-3 text-end font-medium">{{ $t('admin.forwarders.won') }}</th>
                <th class="px-5 py-3 text-end font-medium">{{ $t('admin.reports.feesPaid') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-line">
              <tr v-for="f in data.top_forwarders" :key="f.name" class="hover:bg-sunken/50">
                <td class="px-5 py-2.5"><NuxtLinkLocale :to="`/admin/forwarders/${f.name}`" class="font-semibold hover:text-sea">{{ f.company_name }}</NuxtLinkLocale></td>
                <td class="px-3 py-2.5 text-end tabular-nums">{{ fmt.number(f.unlocks) }}</td>
                <td class="px-3 py-2.5 text-end tabular-nums">{{ fmt.number(f.quotes) }}</td>
                <td class="px-3 py-2.5 text-end tabular-nums">{{ fmt.number(f.won) }}</td>
                <td class="px-5 py-2.5 text-end font-semibold tabular-nums">{{ fmt.money(f.fees, cur) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <EmptyState v-else icon="building" :title="$t('admin.reports.noData')" />
      </section>
    </template>
  </div>
</template>
