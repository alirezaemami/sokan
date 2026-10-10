<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'admin' })
const { t } = useI18n()
useHead({ title: t('admin.nav.forwarders') })
const api = useSokan()
const fmt = useFormat()
const countryLabel = useCountryLabel()
const route = useRoute()

const status = ref(String(route.query.status || ''))
const search = ref('')
const q = refDebounced(search, 300)
const page = ref(1)
watch([status, q], () => (page.value = 1))

const { data, status: loading } = await useAsyncData(
  'admin-forwarders',
  () => api.admin.forwarders({ status: status.value || undefined, search: q.value || undefined, page: page.value }),
  { server: false, watch: [status, q, page] },
)

const tabs = computed(() => {
  const c = data.value?.counts || {}
  return [
    { value: '', label: t('common.all'), count: Object.values(c).reduce((a, b) => a + b, 0) },
    ...['Pending', 'Active', 'Suspended', 'Rejected'].map((s) => ({ value: s, label: t(`status.${s}`), count: c[s] || 0 })),
  ]
})
</script>

<template>
  <div>
    <PortalHeading :title="$t('admin.nav.forwarders')" :subtitle="$t('admin.forwarders.subtitle')" />
    <FilterTabs v-model="status" :options="tabs" />
    <FormField v-model="search" type="search" icon="search" class="mb-5 max-w-md" :placeholder="$t('admin.forwarders.search')" />

    <div v-if="loading === 'pending' && !data" class="space-y-3"><div v-for="i in 5" :key="i" class="skeleton h-20" /></div>
    <div v-else-if="data?.items.length" class="card divide-y divide-line overflow-hidden p-0">
      <NuxtLinkLocale
        v-for="f in data.items"
        :key="f.name"
        :to="`/admin/forwarders/${f.name}`"
        class="grid grid-cols-[auto_1fr_auto] items-center gap-x-4 gap-y-1 px-4 py-4 hover:bg-sunken/60 sm:px-5 md:grid-cols-[auto_minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)_auto]"
      >
        <CompanyAvatar :name="f.company_name" :logo="f.logo" size="sm" class="row-span-2 md:row-span-1" />
        <div class="min-w-0">
          <p class="flex items-center gap-1.5 truncate font-semibold">
            <span class="truncate">{{ f.company_name }}</span>
            <AppIcon v-if="f.is_verified" name="badge-check" :size="15" class="shrink-0 text-sea" />
            <AppIcon v-if="f.is_featured" name="sparkles" :size="15" class="shrink-0 text-warning" />
          </p>
          <p class="truncate text-xs text-faint">{{ [f.city, countryLabel(f.country)].filter(Boolean).join(', ') }} · {{ f.email }}<span v-if="f.email_verified === false" class="ms-1 rounded-full bg-warning/15 px-1.5 py-px text-[11px] font-semibold text-warning">{{ $t('admin.emailUnverified.badge') }}</span></p>
        </div>
        <div class="col-start-2 text-xs text-muted md:col-start-auto">
          <span class="md:block">{{ f.plan }}</span>
          <span class="md:hidden"> · </span>
          <span class="tabular-nums">{{ fmt.money(f.wallet_balance, f.wallet_currency || 'USD') }}</span>
        </div>
        <div class="hidden text-xs text-muted tabular-nums md:block">
          {{ $t('admin.forwarders.quotesWon', { q: f.quotes_sent, w: f.quotes_won }) }}
          <span v-if="f.review_count" class="block">★ {{ fmt.number(f.rating, 1) }} ({{ f.review_count }})</span>
        </div>
        <div class="col-start-3 row-start-1 md:col-start-auto md:row-start-auto"><StatusPill :status="f.status" /></div>
      </NuxtLinkLocale>
    </div>
    <div v-else class="card"><EmptyState icon="building" :title="$t('admin.forwarders.empty')" /></div>
    <AppPagination v-if="data" v-model="page" class="mt-6" :total="data.total" :page-size="20" />
  </div>
</template>
