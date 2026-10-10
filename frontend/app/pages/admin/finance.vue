<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'admin' })
const { t } = useI18n()
useHead({ title: t('admin.nav.finance') })
const api = useSokan()
const fmt = useFormat()
const toast = useToast()
const errorMessage = useErrorMessage()
const route = useRoute()

const TYPES = ['Top-up', 'Request Unlock', 'Quote Fee', 'Subscription', 'Signup Bonus', 'Refund', 'Adjustment']
const filters = reactive({
  forwarder: String(route.query.forwarder || ''),
  transaction_type: '',
  from_date: '',
  to_date: '',
})
const page = ref(1)
watch(filters, () => (page.value = 1))
const params = () => ({
  forwarder: filters.forwarder || undefined,
  transaction_type: filters.transaction_type || undefined,
  from_date: filters.from_date || undefined,
  to_date: filters.to_date || undefined,
})

const { data, status: loading } = await useAsyncData('admin-ledger', () => api.admin.transactions({ ...params(), page: page.value }), {
  server: false,
  watch: [filters, page],
})
const cur = computed(() => data.value?.currency || 'USD')

// Export every row matching the filters, not just the visible page.
const exporting = ref(false)
async function exportCsv() {
  exporting.value = true
  try {
    const rows: Record<string, any>[] = []
    for (let p = 1; p <= 200; p++) {
      const res = await api.admin.transactions({ ...params(), page: p, page_size: 100 })
      rows.push(...res.items)
      if (rows.length >= res.total || !res.items.length) break
    }
    downloadCsv(
      `sokan-ledger-${new Date().toISOString().slice(0, 10)}.csv`,
      [
        { key: 'posting_date', label: t('admin.finance.date') },
        { key: 'name', label: 'ID' },
        { key: 'company_name', label: t('admin.finance.forwarder') },
        { key: 'transaction_type', label: t('admin.finance.type') },
        { key: 'amount', label: t('wallet.amount') },
        { key: 'balance_after', label: t('admin.finance.balanceAfter') },
        { key: 'currency', label: t('fields.currency') },
        { key: 'description', label: t('admin.finance.description') },
      ],
      rows,
    )
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <div>
    <PortalHeading :title="$t('admin.nav.finance')" :subtitle="$t('admin.finance.subtitle')">
      <AppButton variant="secondary" icon="upload" :loading="exporting" :disabled="!data?.total" @click="exportCsv">{{ $t('admin.exportCsv') }}</AppButton>
    </PortalHeading>

    <div class="card mb-5 grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4">
      <FormField v-model="filters.transaction_type" as="select" :label="$t('admin.finance.type')">
        <template #options>
          <option value="">{{ $t('common.all') }}</option>
          <option v-for="ty in TYPES" :key="ty" :value="ty">{{ fmt.label('txn', ty) }}</option>
        </template>
      </FormField>
      <FormField v-model="filters.from_date" type="date" :label="$t('common.from')" />
      <FormField v-model="filters.to_date" type="date" :label="$t('common.to')" />
      <FormField v-model="filters.forwarder" :label="$t('admin.finance.forwarderId')" placeholder="FWD-00001" />
    </div>

    <div v-if="data" class="mb-5 grid grid-cols-3 gap-3">
      <div class="card p-4"><p class="font-display text-2xl text-success tabular-nums">+{{ fmt.money(data.credits, cur) }}</p><p class="text-xs text-muted">{{ $t('admin.finance.credits') }}</p></div>
      <div class="card p-4"><p class="font-display text-2xl tabular-nums">{{ fmt.money(data.debits, cur) }}</p><p class="text-xs text-muted">{{ $t('admin.finance.debits') }}</p></div>
      <div class="card p-4"><p class="font-display text-2xl tabular-nums">{{ fmt.number(data.total) }}</p><p class="text-xs text-muted">{{ $t('admin.finance.count') }}</p></div>
    </div>

    <div v-if="loading === 'pending' && !data" class="skeleton h-96" />
    <div v-else-if="data?.items.length" class="card overflow-x-auto p-0">
      <table class="w-full min-w-[640px] text-sm">
        <thead>
          <tr class="border-b border-line text-start text-xs text-faint">
            <th class="px-4 py-3 text-start font-medium">{{ $t('admin.finance.date') }}</th>
            <th class="px-4 py-3 text-start font-medium">{{ $t('admin.finance.forwarder') }}</th>
            <th class="px-4 py-3 text-start font-medium">{{ $t('admin.finance.type') }}</th>
            <th class="px-4 py-3 text-end font-medium">{{ $t('wallet.amount') }}</th>
            <th class="px-4 py-3 text-end font-medium">{{ $t('admin.finance.balanceAfter') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-line">
          <tr v-for="tx in data.items" :key="tx.name" class="hover:bg-sunken/50">
            <td class="px-4 py-3 whitespace-nowrap text-muted">{{ fmt.date(tx.posting_date, 'short') }}</td>
            <td class="max-w-56 px-4 py-3">
              <NuxtLinkLocale :to="`/admin/forwarders/${tx.forwarder}`" class="block truncate font-semibold hover:text-sea">{{ tx.company_name }}</NuxtLinkLocale>
              <span v-if="tx.description" class="block truncate text-xs text-faint">{{ tx.description }}</span>
            </td>
            <td class="px-4 py-3 whitespace-nowrap">{{ fmt.label('txn', tx.transaction_type) }}</td>
            <td class="px-4 py-3 text-end font-semibold whitespace-nowrap tabular-nums" :class="tx.amount > 0 ? 'text-success' : ''">{{ tx.amount > 0 ? '+' : '' }}{{ fmt.money(tx.amount, tx.currency) }}</td>
            <td class="px-4 py-3 text-end whitespace-nowrap text-muted tabular-nums">{{ fmt.money(tx.balance_after, tx.currency) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="card"><EmptyState icon="receipt" :title="$t('admin.finance.empty')" /></div>
    <AppPagination v-if="data" v-model="page" class="mt-6" :total="data.total" :page-size="50" />
  </div>
</template>
