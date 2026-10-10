<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'customer' })
const { t } = useI18n()
useHead({ title: t('portal.nav.overview') })
const api = useSokan()
const fmt = useFormat()
const { me } = useAuth()

const { data, status } = await useAsyncData('cust-dash', () => api.customer.dashboard(), { server: false })
const c = computed(() => data.value?.counts ?? {})
</script>

<template>
  <div>
    <PortalHeading :title="$t('portal.hello', { name: me?.full_name?.split(' ')[0] || '' })" :subtitle="$t('account.subtitle')">
      <AppButton to="/get-quote" variant="accent" icon="plus">{{ $t('portal.nav.newRequest') }}</AppButton>
    </PortalHeading>

    <div v-if="me?.customer?.is_blocked" class="mb-6 rounded-2xl bg-danger/10 p-4 text-sm text-danger">{{ $t('account.blocked') }}</div>

    <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <StatTile icon="send" :label="$t('account.open')" :value="fmt.number(c.Open || 0)" />
      <StatTile icon="receipt" tone="buoy" :label="$t('account.quotesWaiting')" :value="fmt.number(data?.quotes_waiting || 0)" />
      <StatTile icon="handshake" tone="success" :label="$t('account.booked')" :value="fmt.number(c.Booked || 0)" />
      <StatTile icon="clock" tone="warning" :label="$t('account.expired')" :value="fmt.number((c.Expired || 0) + (c.Cancelled || 0))" />
    </div>

    <div class="mt-10 flex items-center justify-between">
      <h2 class="text-lg font-bold">{{ $t('account.recent') }}</h2>
      <NuxtLinkLocale to="/account/requests" class="text-sm font-semibold text-sea">{{ $t('common.viewAll') }}</NuxtLinkLocale>
    </div>
    <div v-if="status === 'pending'" class="mt-4 grid gap-4 md:grid-cols-2"><div v-for="i in 2" :key="i" class="skeleton h-48" /></div>
    <div v-else-if="data?.recent.length" class="mt-4 grid gap-4 md:grid-cols-2">
      <RequestRow v-for="r in data.recent" :key="r.name" :r="r" />
    </div>
    <div v-else class="card mt-4">
      <EmptyState icon="send" :title="$t('account.emptyTitle')" :text="$t('account.emptyText')">
        <AppButton to="/get-quote" variant="primary" icon-end="arrow-right">{{ $t('nav.getQuoteFree') }}</AppButton>
      </EmptyState>
    </div>
  </div>
</template>
