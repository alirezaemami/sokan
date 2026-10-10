<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'admin' })
const { t } = useI18n()
useHead({ title: t('admin.nav.requests') })
const api = useSokan()
const fmt = useFormat()
const countryLabel = useCountryLabel()
const route = useRoute()
const { modes, load: loadModes } = useModes()
onMounted(loadModes)

const status = ref(String(route.query.status || ''))
const mode = ref('')
const customer = ref(String(route.query.customer || ''))
const search = ref('')
const q = refDebounced(search, 300)
const page = ref(1)
watch([status, mode, q], () => (page.value = 1))

const { data, status: loading } = await useAsyncData(
  'admin-requests',
  () =>
    api.admin.requests({
      status: status.value || undefined,
      mode: mode.value || undefined,
      customer: customer.value || undefined,
      search: q.value || undefined,
      page: page.value,
    }),
  { server: false, watch: [status, mode, q, page, customer] },
)

const tabs = computed(() => {
  const c = data.value?.counts || {}
  return [
    { value: '', label: t('common.all'), count: Object.values(c).reduce((a, b) => a + b, 0) },
    ...['Open', 'Booked', 'Draft', 'Expired', 'Cancelled'].map((s) => ({ value: s, label: t(`status.${s}`), count: c[s] || 0 })),
  ]
})
</script>

<template>
  <div>
    <PortalHeading :title="$t('admin.nav.requests')" :subtitle="$t('admin.requests.subtitle')" />
    <FilterTabs v-model="status" :options="tabs" />
    <div class="mb-5 grid gap-3 sm:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
      <FormField v-model="search" type="search" icon="search" :placeholder="$t('admin.requests.search')" />
      <FormField v-model="mode" as="select">
        <template #options>
          <option value="">{{ $t('directory.allModes') }}</option>
          <option v-for="m in modes" :key="m.name" :value="m.name">{{ $t(`modes.${m.code}.name`) }}</option>
        </template>
      </FormField>
    </div>
    <p v-if="customer" class="mb-4 flex items-center gap-2 text-sm text-muted">
      {{ $t('admin.requests.forCustomer', { name: customer }) }}
      <button type="button" class="font-semibold text-sea hover:underline" @click="customer = ''">{{ $t('admin.clearFilter') }}</button>
    </p>

    <div v-if="loading === 'pending' && !data" class="space-y-3"><div v-for="i in 5" :key="i" class="skeleton h-20" /></div>
    <div v-else-if="data?.items.length" class="card divide-y divide-line overflow-hidden p-0">
      <NuxtLinkLocale
        v-for="r in data.items"
        :key="r.name"
        :to="`/admin/requests/${r.name}`"
        class="grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-1 px-4 py-4 hover:bg-sunken/60 sm:px-5 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)_auto]"
      >
        <div class="min-w-0">
          <p class="truncate font-semibold">{{ r.title }}</p>
          <p class="truncate text-xs text-faint">
            <span class="font-mono">{{ r.name }}</span> · {{ r.customer_name }} · {{ fmt.relative(r.creation) }}
          </p>
        </div>
        <p class="col-span-2 truncate text-xs text-muted md:col-span-1">{{ countryLabel(r.origin_country, { flag: true }) }} → {{ countryLabel(r.destination_country, { flag: true }) }}</p>
        <p class="hidden text-xs text-muted tabular-nums md:block">
          {{ $t('admin.requests.funnel', { leads: r.leads_sent, unlocks: r.unlock_count, quotes: r.quote_count }) }}
        </p>
        <div class="col-start-2 row-start-1 md:col-start-auto md:row-start-auto"><StatusPill :status="r.status" /></div>
      </NuxtLinkLocale>
    </div>
    <div v-else class="card"><EmptyState icon="inbox" :title="$t('admin.requests.empty')" /></div>
    <AppPagination v-if="data" v-model="page" class="mt-6" :total="data.total" :page-size="20" />
  </div>
</template>
