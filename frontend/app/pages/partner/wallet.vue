<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'forwarder' })
const { t } = useI18n()
useHead({ title: t('portal.nav.wallet') })
const api = useSokan()
const fmt = useFormat()
const toast = useToast()
const errorMessage = useErrorMessage()
const { me, refresh: refreshMe } = useAuth()

const page = ref(1)
const { data, refresh } = await useAsyncData('partner-wallet', () => api.partner.wallet({ page: page.value }), { server: false, watch: [page] })
const { data: plans } = await useAsyncData('plans', () => api.plans(), { server: false })
const s = computed(() => data.value?.summary)

// ---- top-up
const topupOpen = ref(false)
const topup = reactive({ amount: 50 as number | null, payment_method: 'Bank Transfer', payment_reference: '' })
const receipt = ref<File | null>(null)
const sending = ref(false)
const PRESETS = [25, 50, 100, 250, 500]

async function sendTopup() {
  sending.value = true
  try {
    const receiptUrl = receipt.value ? await uploadFile(receipt.value, { isPrivate: true, csrf: me.value?.csrf_token }) : undefined
    await api.partner.topup({ ...topup, receipt: receiptUrl })
    toast.success(t('wallet.topupSent'))
    topupOpen.value = false
    receipt.value = null
    await refresh()
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    sending.value = false
  }
}

// ---- plan
const planBusy = ref('')
async function choosePlan(name: string) {
  planBusy.value = name
  try {
    await api.partner.changePlan(name)
    toast.success(t('wallet.planChanged', { plan: name }))
    await Promise.all([refresh(), refreshMe()])
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    planBusy.value = ''
  }
}
</script>

<template>
  <div>
    <PortalHeading :title="$t('portal.nav.wallet')">
      <AppButton variant="accent" icon="plus" @click="topupOpen = true">{{ $t('portal.topUp') }}</AppButton>
    </PortalHeading>

    <div v-if="!s" class="grid gap-4 md:grid-cols-3"><div v-for="i in 3" :key="i" class="skeleton h-36" /></div>
    <template v-else>
      <div class="grid gap-4 md:grid-cols-3">
        <div class="relative overflow-hidden rounded-3xl bg-brand-gradient p-6 text-white md:col-span-1">
          <div class="absolute -end-10 -top-10 size-40 rounded-full bg-white/10 blur-2xl" />
          <p class="relative text-sm text-white/75">{{ $t('portal.walletBalance') }}</p>
          <p class="relative mt-2 text-4xl font-black tabular-nums">{{ fmt.money(s.balance, s.currency) }}</p>
          <p v-if="s.low_balance" class="relative mt-2 inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-1 text-xs font-semibold"><AppIcon name="alert" :size="13" /> {{ $t('wallet.low') }}</p>
        </div>
        <StatTile icon="lock-open" :label="$t('partner.freeUnlocks')" :value="fmt.number(s.free_views_left)" :hint="$t('partner.thenFee', { fee: fmt.money(s.view_fee, s.currency) })" />
        <StatTile icon="send" tone="coral" :label="$t('wallet.freeQuotes')" :value="fmt.number(s.free_quotes_left)" :hint="$t('partner.thenFee', { fee: fmt.money(s.quote_fee, s.currency) })" />
      </div>

      <!-- Pending top-ups -->
      <div v-if="data?.topups.some((x) => x.status === 'Pending')" class="mt-6 space-y-2">
        <div v-for="tp in data.topups.filter((x) => x.status === 'Pending')" :key="tp.name" class="flex items-center justify-between gap-3 rounded-2xl bg-warning/10 p-4 text-sm">
          <span class="flex items-center gap-2"><AppIcon name="clock" :size="16" class="text-warning" /> {{ $t('wallet.pending', { amount: fmt.money(tp.amount, tp.currency) }) }}</span>
          <span class="text-xs text-faint">{{ fmt.relative(tp.creation) }}</span>
        </div>
      </div>

      <!-- Plans -->
      <section v-if="plans?.length" class="mt-10">
        <h2 class="text-lg font-bold">{{ $t('wallet.plans') }}</h2>
        <p class="mt-1 text-sm text-muted">{{ $t('wallet.plansText') }}</p>
        <div class="mt-5 grid gap-4 lg:grid-cols-3">
          <PlanCard v-for="pl in plans" :key="pl.name" :plan="pl" :current="pl.name === s.plan" :highlight="pl.name === s.plan">
            <AppButton v-if="pl.name === s.plan" block variant="glass" disabled icon="check">{{ $t('pricing.current') }}</AppButton>
            <AppButton v-else block variant="secondary" :loading="planBusy === pl.name" @click="choosePlan(pl.name)">
              {{ pl.monthly_fee ? $t('wallet.switchPaid', { fee: fmt.money(pl.monthly_fee, pl.currency) }) : $t('wallet.switch') }}
            </AppButton>
          </PlanCard>
        </div>
      </section>

      <!-- Ledger -->
      <section class="mt-10">
        <h2 class="text-lg font-bold">{{ $t('wallet.history') }}</h2>
        <div v-if="data?.transactions.length" class="card mt-4 divide-y divide-line">
          <div v-for="tx in data.transactions" :key="tx.name" class="flex items-center gap-4 p-4">
            <span class="grid size-10 shrink-0 place-items-center rounded-xl" :class="tx.amount > 0 ? 'bg-success/12 text-success' : 'bg-sunken text-ink-soft'">
              <AppIcon :name="tx.amount > 0 ? 'plus' : tx.transaction_type === 'Request Unlock' ? 'lock-open' : tx.transaction_type === 'Quote Fee' ? 'send' : 'receipt'" :size="18" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold">{{ fmt.label('txn', tx.transaction_type) }}</p>
              <p class="truncate text-xs text-faint">{{ tx.description }} · {{ fmt.date(tx.posting_date, 'short') }}</p>
            </div>
            <div class="text-end">
              <p class="font-bold tabular-nums" :class="tx.amount > 0 ? 'text-success' : ''">{{ tx.amount > 0 ? '+' : '' }}{{ fmt.money(tx.amount, tx.currency) }}</p>
              <p class="text-xs text-faint tabular-nums">{{ fmt.money(tx.balance_after, tx.currency) }}</p>
            </div>
          </div>
        </div>
        <div v-else class="card mt-4"><EmptyState icon="wallet" :title="$t('wallet.emptyTitle')" :text="$t('wallet.emptyText')" /></div>
        <AppPagination v-if="data" v-model="page" class="mt-6" :total="data.total" :page-size="25" />
      </section>
    </template>

    <AppModal v-model="topupOpen" :title="$t('wallet.topupTitle')">
      <div class="space-y-5">
        <div class="flex flex-wrap gap-2">
          <button v-for="a in PRESETS" :key="a" type="button" class="rounded-xl px-4 py-2 text-sm font-bold transition-all" :class="topup.amount === a ? 'bg-brand text-white' : 'bg-sunken hover:bg-brand/10'" @click="topup.amount = a">
            {{ fmt.money(a, s?.currency || 'USD') }}
          </button>
        </div>
        <FormField v-model.number="topup.amount" type="number" min="1" inputmode="decimal" :label="$t('wallet.amount')" :suffix="s?.currency" required />
        <FormField v-model="topup.payment_method" as="select" :label="$t('wallet.method')">
          <template #options><option v-for="m in ['Bank Transfer', 'Card', 'Cash']" :key="m" :value="m">{{ fmt.label('payment', m) }}</option></template>
        </FormField>
        <div v-if="data?.instructions" class="rounded-xl bg-sunken p-4 text-sm leading-relaxed" v-html="data.instructions" />
        <FormField v-model="topup.payment_reference" :label="$t('wallet.reference')" :hint="$t('wallet.referenceHint')" />
        <label class="flex cursor-pointer items-center gap-3 rounded-xl border-2 border-dashed border-line-strong p-4 text-sm hover:border-brand/50">
          <AppIcon name="upload" :size="18" class="text-faint" />
          <span class="flex-1 truncate">{{ receipt ? receipt.name : $t('wallet.receipt') }}</span>
          <input type="file" class="sr-only" accept=".pdf,.jpg,.jpeg,.png" @change="receipt = ($event.target as HTMLInputElement).files?.[0] ?? null" />
        </label>
      </div>
      <template #footer>
        <AppButton variant="ghost" @click="topupOpen = false">{{ $t('common.cancel') }}</AppButton>
        <AppButton variant="primary" :loading="sending" :disabled="!topup.amount" @click="sendTopup">{{ $t('wallet.submitTopup') }}</AppButton>
      </template>
    </AppModal>
  </div>
</template>
