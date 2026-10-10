<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'forwarder' })
const { t } = useI18n()
useHead({ title: t('portal.nav.overview') })
const api = useSokan()
const fmt = useFormat()

const { data, status } = await useAsyncData('partner-dash', () => api.partner.dashboard(), { server: false })
const company = computed(() => data.value?.company)
const s = computed(() => data.value?.stats)
const w = computed(() => data.value?.wallet)
</script>

<template>
  <div>
    <div v-if="status === 'pending' && !data" class="space-y-4"><div class="skeleton h-28" /><div class="grid grid-cols-2 gap-3 lg:grid-cols-4"><div v-for="i in 4" :key="i" class="skeleton h-32" /></div></div>

    <template v-else-if="data && company && s && w">
      <!-- Account state banners -->
      <div v-if="company.status === 'Pending'" class="mb-6 flex items-start gap-4 rounded-2xl bg-warning/12 p-5">
        <AppIcon name="clock" class="mt-0.5 shrink-0 text-warning" />
        <div>
          <p class="font-bold">{{ $t('partner.pendingTitle') }}</p>
          <p class="mt-1 text-sm text-ink-soft">{{ $t('partner.pendingText') }}</p>
          <AppButton to="/partner/profile" size="sm" variant="secondary" class="mt-3">{{ $t('partner.completeProfile') }}</AppButton>
        </div>
      </div>
      <div v-else-if="company.status !== 'Active'" class="mb-6 rounded-2xl bg-danger/10 p-5 text-sm">
        <p class="font-bold text-danger">{{ $t(`partner.status.${company.status}`) }}</p>
        <p v-if="company.rejection_reason" class="mt-1">{{ company.rejection_reason }}</p>
      </div>

      <!-- Hero row -->
      <div class="relative mb-6 overflow-hidden rounded-3xl bg-night-950 p-6 text-white sm:p-8">
        <AuroraBackground :grid="false" />
        <div class="relative flex flex-wrap items-center justify-between gap-6">
          <div>
            <p class="text-sm text-white/60">{{ $t('partner.actionable') }}</p>
            <p class="mt-1 text-5xl font-black tabular-nums"><CountUp :to="s.actionable" /></p>
            <p class="mt-1 text-sm text-white/60">{{ $t('partner.actionableHint') }}</p>
          </div>
          <div class="flex flex-wrap gap-3">
            <AppButton to="/partner/leads" variant="accent" size="lg" icon-end="arrow-right">{{ $t('partner.openLeads') }}</AppButton>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile icon="wallet" tone="lagoon" :label="$t('portal.walletBalance')" :value="fmt.money(w.balance, w.currency)" :hint="w.plan ? `${w.plan}` : undefined" />
        <StatTile icon="lock-open" :label="$t('partner.freeUnlocks')" :value="fmt.number(w.free_views_left)" :hint="$t('partner.thenFee', { fee: fmt.money(w.view_fee, w.currency) })" />
        <StatTile icon="send" tone="coral" :label="$t('partner.quotesSent')" :value="fmt.number(s.quotes_sent)" />
        <StatTile icon="award" tone="success" :label="$t('partner.winRate')" :value="`${fmt.number(s.win_rate)}%`" :hint="$t('partner.won', { n: fmt.number(s.quotes_won) })" />
      </div>

      <div v-if="w.low_balance" class="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-coral/10 p-5">
        <p class="flex items-center gap-2 text-sm font-semibold"><AppIcon name="alert" class="text-coral" /> {{ $t('partner.lowBalance') }}</p>
        <AppButton to="/partner/wallet" size="sm" variant="accent">{{ $t('portal.topUp') }}</AppButton>
      </div>

      <div v-if="company.profile_complete < 100" class="card mt-6 p-5">
        <div class="flex items-center justify-between gap-4">
          <p class="text-sm font-semibold">{{ $t('partner.profileStrength') }}</p>
          <span class="text-sm font-bold text-brand">{{ fmt.number(company.profile_complete) }}%</span>
        </div>
        <div class="mt-3 h-2 overflow-hidden rounded-full bg-sunken"><div class="h-full rounded-full bg-brand-gradient transition-all duration-1000" :style="{ width: `${company.profile_complete}%` }" /></div>
        <p class="mt-3 text-xs text-muted">{{ $t('partner.profileHint') }} <NuxtLinkLocale to="/partner/profile" class="font-semibold text-brand">{{ $t('common.edit') }}</NuxtLinkLocale></p>
      </div>

      <div class="mt-10 flex items-center justify-between">
        <h2 class="text-lg font-bold">{{ $t('partner.latest') }}</h2>
        <NuxtLinkLocale to="/partner/leads" class="text-sm font-semibold text-brand">{{ $t('common.viewAll') }}</NuxtLinkLocale>
      </div>
      <div v-if="data.recent.length" class="mt-4 grid gap-4 md:grid-cols-2">
        <LeadCard v-for="r in data.recent" :key="r.name" :r="r" />
      </div>
      <div v-else class="card mt-4"><EmptyState icon="inbox" :title="$t('leads.emptyTitle')" :text="$t('leads.emptyText')" /></div>
    </template>
  </div>
</template>
