<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'customer' })
const { t } = useI18n()
useHead({ title: t('portal.nav.requests') })
const api = useSokan()

const status = ref('')
const page = ref(1)
const { data, status: loading } = await useAsyncData('cust-requests', () => api.customer.requests({ status: status.value || undefined, page: page.value }), {
  server: false,
  watch: [status, page],
})
watch(status, () => (page.value = 1))

const tabs = computed(() => [
  { value: '', label: t('common.all') },
  ...['Open', 'Booked', 'Draft', 'Expired', 'Cancelled'].map((s) => ({ value: s, label: t(`status.${s}`) })),
])
</script>

<template>
  <div>
    <PortalHeading :title="$t('portal.nav.requests')">
      <AppButton to="/get-quote" variant="accent" icon="plus">{{ $t('portal.nav.newRequest') }}</AppButton>
    </PortalHeading>
    <FilterTabs v-model="status" :options="tabs" />
    <div v-if="loading === 'pending' && !data" class="grid gap-4 md:grid-cols-2"><div v-for="i in 4" :key="i" class="skeleton h-48" /></div>
    <div v-else-if="data?.items.length" class="grid gap-4 md:grid-cols-2">
      <RequestRow v-for="r in data.items" :key="r.name" :r="r" />
    </div>
    <div v-else class="card"><EmptyState icon="inbox" :title="$t('account.noneTitle')" :text="$t('account.noneText')" /></div>
    <AppPagination v-if="data" v-model="page" class="mt-8" :total="data.total" :page-size="20" />
  </div>
</template>
