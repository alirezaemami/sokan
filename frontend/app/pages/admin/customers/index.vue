<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'admin' })
const { t } = useI18n()
useHead({ title: t('admin.nav.customers') })
const api = useSokan()
const fmt = useFormat()
const countryLabel = useCountryLabel()

const blocked = ref('')
const search = ref('')
const q = refDebounced(search, 300)
const page = ref(1)
watch([blocked, q], () => (page.value = 1))

const { data, status: loading } = await useAsyncData(
  'admin-customers',
  () => api.admin.customers({ blocked: blocked.value === '' ? undefined : blocked.value, search: q.value || undefined, page: page.value }),
  { server: false, watch: [blocked, q, page] },
)
const tabs = computed(() => [
  { value: '', label: t('common.all') },
  { value: '0', label: t('admin.customers.active') },
  { value: '1', label: t('admin.customers.blocked') },
])
</script>

<template>
  <div>
    <PortalHeading :title="$t('admin.nav.customers')" :subtitle="$t('admin.customers.subtitle')" />
    <FilterTabs v-model="blocked" :options="tabs" />
    <FormField v-model="search" type="search" icon="search" class="mb-5 max-w-md" :placeholder="$t('admin.customers.search')" />

    <div v-if="loading === 'pending' && !data" class="space-y-3"><div v-for="i in 5" :key="i" class="skeleton h-16" /></div>
    <div v-else-if="data?.items.length" class="card divide-y divide-line overflow-hidden p-0">
      <NuxtLinkLocale
        v-for="c in data.items"
        :key="c.name"
        :to="`/admin/customers/${c.name}`"
        class="grid grid-cols-[auto_1fr_auto] items-center gap-x-4 gap-y-1 px-4 py-3.5 hover:bg-sunken/60 sm:px-5 md:grid-cols-[auto_minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)_auto]"
      >
        <span class="row-span-2 grid size-9 place-items-center rounded-full bg-sea/10 text-sm font-bold text-sea md:row-span-1">{{ (c.full_name || '?').charAt(0) }}</span>
        <div class="min-w-0">
          <p class="truncate font-semibold">{{ c.full_name }}<span v-if="c.company_name" class="font-normal text-muted"> · {{ c.company_name }}</span></p>
          <p class="truncate text-xs text-faint">{{ c.email }}<template v-if="c.phone"> · {{ c.phone }}</template><span v-if="c.email_verified === false" class="ms-1 rounded-full bg-warning/15 px-1.5 py-px text-[11px] font-semibold text-warning">{{ $t('admin.emailUnverified.badge') }}</span></p>
        </div>
        <p class="col-start-2 truncate text-xs text-muted md:col-start-auto">{{ countryLabel(c.country, { flag: true }) || '—' }}</p>
        <p class="hidden text-xs text-muted tabular-nums md:block">{{ $t('admin.customers.counts', { r: c.requests_count, b: c.bookings_count }) }}</p>
        <div class="col-start-3 row-start-1 md:col-start-auto md:row-start-auto">
          <span v-if="c.is_blocked" class="rounded-full bg-danger/12 px-2.5 py-1 text-xs font-semibold text-danger">{{ $t('admin.customers.blockedOne') }}</span>
          <span v-else class="text-xs text-faint">{{ fmt.date(c.creation, 'short') }}</span>
        </div>
      </NuxtLinkLocale>
    </div>
    <div v-else class="card"><EmptyState icon="users" :title="$t('admin.customers.empty')" /></div>
    <AppPagination v-if="data" v-model="page" class="mt-6" :total="data.total" :page-size="20" />
  </div>
</template>
