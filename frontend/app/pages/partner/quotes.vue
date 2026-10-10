<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'forwarder' })
const { t } = useI18n()
useHead({ title: t('portal.nav.quotes') })
const api = useSokan()
const fmt = useFormat()

const status = ref('')
const page = ref(1)
const { data, status: loading } = await useAsyncData('partner-quotes', () => api.partner.quotes({ status: status.value || undefined, page: page.value }), {
  server: false,
  watch: [status, page],
})
watch(status, () => (page.value = 1))
const tabs = computed(() => [
  { value: '', label: t('common.all') },
  ...['Submitted', 'Accepted', 'Rejected', 'Expired', 'Withdrawn'].map((s) => ({ value: s, label: t(`status.${s}`) })),
])
</script>

<template>
  <div>
    <PortalHeading :title="$t('portal.nav.quotes')" />
    <FilterTabs v-model="status" :options="tabs" />
    <div v-if="loading === 'pending' && !data" class="space-y-3"><div v-for="i in 5" :key="i" class="skeleton h-20" /></div>
    <div v-else-if="data?.items.length" class="card divide-y divide-line">
      <NuxtLinkLocale v-for="q in data.items" :key="q.name" :to="`/partner/leads/${q.request}`" class="flex flex-wrap items-center gap-4 p-4 transition-colors hover:bg-sunken/60 sm:p-5">
        <div class="min-w-0 flex-1">
          <p class="truncate font-semibold">{{ q.request_title }}</p>
          <p class="mt-0.5 text-xs text-faint">{{ q.name }} · {{ fmt.relative(q.creation) }}</p>
        </div>
        <p class="font-extrabold tabular-nums">{{ fmt.money(q.total_amount, q.currency) }}</p>
        <StatusPill :status="q.status" />
      </NuxtLinkLocale>
    </div>
    <div v-else class="card"><EmptyState icon="receipt" :title="$t('partner.noQuotesTitle')" :text="$t('partner.noQuotesText')" /></div>
    <AppPagination v-if="data" v-model="page" class="mt-8" :total="data.total" :page-size="20" />
  </div>
</template>
