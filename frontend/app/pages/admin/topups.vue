<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'admin' })
const { t } = useI18n()
useHead({ title: t('admin.nav.topups') })
const api = useSokan()
const fmt = useFormat()
const toast = useToast()
const errorMessage = useErrorMessage()
const { refresh: refreshCounts } = useAdminAttention()

const status = ref('Pending')
const page = ref(1)
watch(status, () => (page.value = 1))
const { data, status: loading, refresh } = await useAsyncData('admin-topups', () => api.admin.topups({ status: status.value, page: page.value }), {
  server: false,
  watch: [status, page],
})
const tabs = computed(() => {
  const c = data.value?.counts || {}
  return [
    ...['Pending', 'Approved', 'Rejected'].map((s) => ({ value: s, label: t(`status.${s}`), count: c[s] || 0 })),
    { value: '', label: t('common.all') },
  ]
})

const target = ref<Record<string, any> | null>(null)
const action = ref<'approve' | 'reject'>('approve')
const open = ref(false)
const busy = ref(false)
function ask(row: Record<string, any>, a: 'approve' | 'reject') {
  target.value = row
  action.value = a
  open.value = true
}
async function confirm(note: string) {
  if (!target.value) return
  busy.value = true
  try {
    await api.admin.reviewTopup(target.value.name, action.value, note || undefined)
    toast.success(action.value === 'approve' ? t('admin.topups.approved') : t('admin.topups.rejected'))
    open.value = false
    await Promise.all([refresh(), refreshCounts()])
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div>
    <PortalHeading :title="$t('admin.nav.topups')" :subtitle="$t('admin.topups.subtitle')" />
    <FilterTabs v-model="status" :options="tabs" />

    <div v-if="loading === 'pending' && !data" class="space-y-3"><div v-for="i in 3" :key="i" class="skeleton h-28" /></div>
    <div v-else-if="data?.items.length" class="space-y-3">
      <article v-for="tp in data.items" :key="tp.name" class="card flex flex-wrap items-center gap-4 p-4 sm:p-5">
        <div class="min-w-0 flex-1 basis-60">
          <NuxtLinkLocale :to="`/admin/forwarders/${tp.forwarder}`" class="font-semibold hover:text-sea">{{ tp.company_name }}</NuxtLinkLocale>
          <p class="mt-0.5 text-xs text-faint">
            <span class="font-mono">{{ tp.name }}</span> · {{ fmt.label('payment', tp.payment_method) }} · {{ fmt.relative(tp.creation) }}
          </p>
          <p v-if="tp.payment_reference" class="mt-1 text-sm text-ink-soft">{{ $t('wallet.reference') }}: <span class="font-mono">{{ tp.payment_reference }}</span></p>
          <p v-if="tp.note" class="mt-1 text-sm text-muted">{{ tp.note }}</p>
          <p v-if="tp.reviewed_by" class="mt-1 text-xs text-faint">{{ $t('admin.reviewedBy', { who: tp.reviewed_by, when: fmt.date(tp.reviewed_on, 'short') }) }}</p>
        </div>
        <div class="text-end">
          <p class="font-display text-2xl tabular-nums">{{ fmt.money(tp.amount, tp.currency) }}</p>
          <p class="text-xs text-faint">{{ $t('admin.topups.balanceNow', { amount: fmt.money(tp.wallet_balance, tp.currency) }) }}</p>
        </div>
        <div class="flex w-full flex-wrap items-center gap-2 sm:w-auto">
          <AppButton v-if="tp.receipt" :href="tp.receipt" variant="ghost" size="sm" icon="file-text">{{ $t('admin.topups.receipt') }}</AppButton>
          <template v-if="tp.status === 'Pending'">
            <AppButton size="sm" variant="danger" @click="ask(tp, 'reject')">{{ $t('admin.reject') }}</AppButton>
            <AppButton size="sm" variant="accent" icon="check" @click="ask(tp, 'approve')">{{ $t('admin.approve') }}</AppButton>
          </template>
          <StatusPill v-else :status="tp.status" />
        </div>
      </article>
    </div>
    <div v-else class="card"><EmptyState icon="credit-card" :title="$t('admin.topups.empty')" /></div>
    <AppPagination v-if="data" v-model="page" class="mt-6" :total="data.total" :page-size="20" />

    <ConfirmDialog
      v-model="open"
      :title="action === 'approve' ? $t('admin.topups.approveTitle') : $t('admin.topups.rejectTitle')"
      :text="target ? $t(action === 'approve' ? 'admin.topups.approveText' : 'admin.topups.rejectText', { amount: fmt.money(target.amount, target.currency), name: target.company_name }) : ''"
      :confirm-label="action === 'approve' ? $t('admin.approve') : $t('admin.reject')"
      :variant="action === 'approve' ? 'accent' : 'danger'"
      :reason="action === 'reject'"
      :reason-hint="$t('admin.reasonShared')"
      :loading="busy"
      @confirm="confirm"
    />
  </div>
</template>
