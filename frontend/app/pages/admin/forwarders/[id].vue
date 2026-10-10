<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'admin' })
const route = useRoute()
const { t } = useI18n()
const api = useSokan()
const fmt = useFormat()
const toast = useToast()
const errorMessage = useErrorMessage()
const countryLabel = useCountryLabel()
const { refresh: refreshCounts } = useAdminAttention()
const id = computed(() => String(route.params.id))

const { data: f, status: loading, error } = await useAsyncData(`admin-fwd-${id.value}`, () => api.admin.forwarder(id.value), { server: false })
const { data: plans } = await useAsyncData('admin-plans', () => api.admin.plans(), { server: false })
useHead({ title: computed(() => f.value?.company_name || t('admin.nav.forwarders')) })

const busy = ref('')
async function run(key: string, call: () => Promise<Record<string, any>>, done?: string) {
  busy.value = key
  try {
    f.value = await call()
    if (done) toast.success(done)
    refreshCounts()
    return true
  } catch (e) {
    toast.error(errorMessage(e))
    return false
  } finally {
    busy.value = ''
  }
}

// ---- email confirmation (a manager can vouch for the address)
const markVerified = () =>
  run(
    'verify',
    async () => {
      await api.admin.markEmailVerified(f.value!.email)
      return api.admin.forwarder(id.value)
    },
    t('admin.emailUnverified.done'),
  )

// ---- status
type Action = { status: string; label: string; variant: 'accent' | 'danger' | 'primary'; reason: boolean }
const actions = computed<Action[]>(() => {
  const s = f.value?.status
  if (s === 'Pending') return [
    { status: 'Active', label: t('admin.forwarders.approve'), variant: 'accent', reason: false },
    { status: 'Rejected', label: t('admin.forwarders.reject'), variant: 'danger', reason: true },
  ]
  if (s === 'Active') return [{ status: 'Suspended', label: t('admin.forwarders.suspend'), variant: 'danger', reason: true }]
  return [{ status: 'Active', label: t('admin.forwarders.reactivate'), variant: 'accent', reason: false }]
})
const pending = ref<Action | null>(null)
const confirmOpen = ref(false)
function ask(a: Action) {
  pending.value = a
  confirmOpen.value = true
}
async function confirmStatus(reason: string) {
  const a = pending.value
  if (!a) return
  const ok = await run('status', () => api.admin.setForwarderStatus(id.value, a.status, reason || undefined), t('admin.forwarders.statusDone', { status: t(`status.${a.status}`) }))
  if (ok) confirmOpen.value = false
}

// ---- flags and plan
const toggle = (field: 'is_verified' | 'is_featured') =>
  run(field, () => api.admin.updateForwarder(id.value, { [field]: f.value?.[field] ? 0 : 1 }), t('common.saved'))
const plan = ref('')
watch(f, (v) => v && (plan.value = v.plan), { immediate: true })
const savePlan = () => run('plan', () => api.admin.updateForwarder(id.value, { plan: plan.value }), t('admin.forwarders.planChanged', { plan: plan.value }))

// ---- wallet adjustment
const adjustOpen = ref(false)
const adjust = reactive({ direction: 'credit' as 'credit' | 'debit', amount: null as number | null, note: '' })
async function saveAdjust() {
  const amount = (adjust.direction === 'debit' ? -1 : 1) * Number(adjust.amount || 0)
  const ok = await run('adjust', () => api.admin.adjustWallet(id.value, amount, adjust.note), t('admin.forwarders.adjusted'))
  if (ok) {
    adjustOpen.value = false
    Object.assign(adjust, { direction: 'credit', amount: null, note: '' })
  }
}

// ---- company details
const editOpen = ref(false)
const edit = reactive<Record<string, string>>({})
const EDITABLE = ['company_name', 'tagline', 'email', 'phone', 'website', 'city', 'country'] as const
function openEdit() {
  EDITABLE.forEach((k) => (edit[k] = f.value?.[k] || ''))
  editOpen.value = true
}
async function saveEdit() {
  if (await run('edit', () => api.admin.updateForwarder(id.value, { ...edit }), t('common.saved'))) editOpen.value = false
}

const facts = computed(() => {
  const v = f.value
  if (!v) return []
  return [
    { label: t('fields.email'), value: v.email, href: v.email ? `mailto:${v.email}` : undefined },
    { label: t('fields.phone'), value: v.phone },
    { label: t('admin.forwarders.website'), value: v.website, href: v.website || undefined },
    { label: t('fields.country'), value: [v.city, countryLabel(v.country)].filter(Boolean).join(', ') },
    { label: t('admin.forwarders.address'), value: v.address },
    { label: t('admin.forwarders.established'), value: v.established_year || null },
    { label: t('admin.forwarders.teamSize'), value: v.team_size },
    { label: t('admin.forwarders.license'), value: v.license_number },
    { label: t('admin.forwarders.licenseDoc'), value: v.license_document ? t('common.view') : null, href: v.license_document || undefined },
    { label: t('admin.forwarders.joined'), value: fmt.date(v.creation) },
  ]
})
const leadTotal = computed(() => Object.values((f.value?.lead_counts || {}) as Record<string, number>).reduce((a, b) => a + b, 0))
</script>

<template>
  <div>
    <PortalHeading :title="f?.company_name || ''" back="/admin/forwarders">
      <template v-if="f">
        <AppButton v-if="f.status === 'Active'" :to="`/forwarders/${f.slug}`" target="_blank" variant="ghost" icon="external-link">{{ $t('admin.forwarders.publicProfile') }}</AppButton>
        <AppButton v-for="a in actions" :key="a.status" :variant="a.variant" @click="ask(a)">{{ a.label }}</AppButton>
      </template>
    </PortalHeading>

    <div v-if="loading === 'pending' && !f" class="grid gap-4 lg:grid-cols-3"><div class="skeleton h-80 lg:col-span-2" /><div class="skeleton h-80" /></div>
    <div v-else-if="error" class="card"><EmptyState icon="alert" :title="$t('admin.notFound')" /></div>
    <template v-else-if="f">
      <div class="mb-6 flex flex-wrap items-center gap-3">
        <CompanyAvatar :name="f.company_name" :logo="f.logo" size="lg" />
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-2">
            <StatusPill :status="f.status" />
            <span v-if="f.is_verified" class="inline-flex items-center gap-1 rounded-full bg-sea/10 px-2.5 py-1 text-xs font-semibold text-sea"><AppIcon name="badge-check" :size="13" /> {{ $t('common.verified') }}</span>
            <span v-if="f.is_featured" class="inline-flex items-center gap-1 rounded-full bg-warning/15 px-2.5 py-1 text-xs font-semibold text-warning"><AppIcon name="sparkles" :size="13" /> {{ $t('admin.forwarders.featured') }}</span>
          </div>
          <p v-if="f.tagline" class="mt-1 text-sm text-muted">{{ f.tagline }}</p>
          <p class="mt-0.5 font-mono text-xs text-faint">{{ f.name }}</p>
        </div>
      </div>
      <div v-if="f.email_verified === false" class="mb-6 flex flex-wrap items-center gap-3 rounded-2xl bg-warning/12 p-4 text-sm">
        <AppIcon name="mail" class="shrink-0 text-warning" />
        <p class="min-w-0 flex-1">{{ $t('admin.emailUnverified.forwarder') }}</p>
        <AppButton size="sm" variant="secondary" icon="check" :loading="busy === 'verify'" @click="markVerified">{{ $t('admin.emailUnverified.mark') }}</AppButton>
      </div>
      <p v-if="f.rejection_reason" class="mb-6 rounded-2xl bg-danger/10 p-4 text-sm text-danger"><b>{{ $t('admin.forwarders.reasonShown') }}</b> {{ f.rejection_reason }}</p>

      <div class="grid gap-4 lg:grid-cols-3">
        <div class="space-y-4 lg:col-span-2">
          <section class="card p-5">
            <div class="mb-4 flex items-center justify-between gap-3">
              <h2 class="font-semibold">{{ $t('admin.forwarders.company') }}</h2>
              <AppButton variant="ghost" size="sm" icon="sliders" @click="openEdit">{{ $t('common.edit') }}</AppButton>
            </div>
            <Facts :items="facts" />
            <p v-if="f.about" class="mt-5 border-t border-line pt-4 text-sm leading-relaxed text-ink-soft">{{ f.about }}</p>
          </section>

          <section class="card p-5">
            <h2 class="font-semibold">{{ $t('admin.forwarders.services') }}</h2>
            <div class="mt-3 flex flex-wrap gap-2">
              <span v-for="s in f.services" :key="s" class="rounded-full bg-sunken px-3 py-1 text-sm">{{ s }}</span>
              <span v-if="!f.services.length" class="text-sm text-faint">—</span>
            </div>
            <h3 class="mt-5 text-sm font-semibold">{{ $t('admin.forwarders.coverage') }}</h3>
            <div class="mt-2 flex flex-wrap gap-2">
              <span v-for="c in f.coverage" :key="c" class="rounded-full bg-sunken px-3 py-1 text-sm">{{ countryLabel(c, { flag: true }) }}</span>
              <span v-if="!f.coverage.length" class="text-sm text-muted">{{ $t('admin.forwarders.worldwide') }}</span>
            </div>
          </section>

          <section class="card p-5">
            <h2 class="font-semibold">{{ $t('admin.forwarders.activity') }}</h2>
            <div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div class="rounded-xl bg-sunken p-3"><p class="font-display text-2xl tabular-nums">{{ fmt.number(leadTotal) }}</p><p class="text-xs text-muted">{{ $t('admin.forwarders.leads') }}</p></div>
              <div class="rounded-xl bg-sunken p-3"><p class="font-display text-2xl tabular-nums">{{ fmt.number(f.leads_unlocked) }}</p><p class="text-xs text-muted">{{ $t('admin.forwarders.unlocked') }}</p></div>
              <div class="rounded-xl bg-sunken p-3"><p class="font-display text-2xl tabular-nums">{{ fmt.number(f.quotes_sent) }}</p><p class="text-xs text-muted">{{ $t('admin.forwarders.quotes') }}</p></div>
              <div class="rounded-xl bg-sunken p-3"><p class="font-display text-2xl tabular-nums">{{ fmt.number(f.quotes_won) }}</p><p class="text-xs text-muted">{{ $t('admin.forwarders.won') }}</p></div>
            </div>
            <ul v-if="f.quotes.length" class="mt-4 divide-y divide-line">
              <li v-for="q in f.quotes" :key="q.name">
                <NuxtLinkLocale :to="`/admin/requests/${q.request}`" class="flex items-center gap-3 py-2.5 text-sm hover:text-sea">
                  <span class="min-w-0 flex-1 truncate font-mono text-xs">{{ q.request }}</span>
                  <span class="tabular-nums">{{ fmt.money(q.total_amount, q.currency) }}</span>
                  <StatusPill :status="q.status" />
                </NuxtLinkLocale>
              </li>
            </ul>
          </section>

          <section class="card p-5">
            <h2 class="font-semibold">{{ $t('admin.forwarders.members') }}</h2>
            <ul class="mt-3 divide-y divide-line">
              <li v-for="m in f.members" :key="m.user" class="flex items-center gap-3 py-2.5">
                <span class="grid size-9 place-items-center rounded-full bg-sea/10 text-sm font-bold text-sea">{{ (m.full_name || m.user).charAt(0) }}</span>
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-semibold">{{ m.full_name || m.user }} <span class="font-normal text-faint">· {{ m.member_role }}</span></p>
                  <p class="truncate text-xs text-faint">{{ m.user }} · {{ m.last_login ? $t('admin.lastLogin', { when: fmt.relative(m.last_login) }) : $t('admin.neverLoggedIn') }}</p>
                </div>
                <span v-if="!m.enabled" class="text-xs text-danger">{{ $t('admin.disabled') }}</span>
              </li>
            </ul>
          </section>
        </div>

        <div class="space-y-4">
          <section class="rounded-2xl bg-night-900 p-5 text-white dark:ring-1 dark:ring-tide/20">
            <p class="text-sm text-white/70">{{ $t('portal.walletBalance') }}</p>
            <p class="font-display mt-1 text-4xl tabular-nums">{{ fmt.money(f.wallet.balance, f.wallet.currency) }}</p>
            <p class="mt-2 text-xs text-white/60">{{ $t('admin.forwarders.freeLeft', { views: f.wallet.free_views_left, quotes: f.wallet.free_quotes_left }) }}</p>
            <AppButton variant="night" size="sm" class="mt-4" icon="sliders" @click="adjustOpen = true">{{ $t('admin.forwarders.adjust') }}</AppButton>
          </section>

          <section class="card space-y-4 p-5">
            <h2 class="font-semibold">{{ $t('admin.forwarders.controls') }}</h2>
            <label v-for="flag in (['is_verified', 'is_featured'] as const)" :key="flag" class="flex cursor-pointer items-center justify-between gap-3">
              <span class="min-w-0">
                <span class="block text-sm font-semibold">{{ $t(`admin.forwarders.${flag}`) }}</span>
                <span class="block text-xs text-faint">{{ $t(`admin.forwarders.${flag}Hint`) }}</span>
              </span>
              <button
                type="button"
                role="switch"
                :aria-checked="!!f[flag]"
                :disabled="busy === flag"
                class="relative h-6 w-11 shrink-0 rounded-full transition-colors"
                :class="f[flag] ? 'bg-sea' : 'bg-line-strong'"
                @click="toggle(flag)"
              >
                <span class="absolute top-0.5 size-5 rounded-full bg-white shadow transition-[inset-inline-start]" :class="f[flag] ? 'start-5.5' : 'start-0.5'" />
              </button>
            </label>
            <div class="border-t border-line pt-4">
              <FormField v-model="plan" as="select" :label="$t('admin.forwarders.plan')">
                <template #options><option v-for="p in plans || []" :key="p.name" :value="p.name">{{ p.plan_name }} · {{ fmt.money(p.monthly_fee, p.currency) }}</option></template>
              </FormField>
              <AppButton v-if="plan !== f.plan" size="sm" class="mt-3" :loading="busy === 'plan'" @click="savePlan">{{ $t('admin.forwarders.changePlan') }}</AppButton>
            </div>
          </section>

          <section class="card p-5">
            <div class="flex items-center justify-between">
              <h2 class="font-semibold">{{ $t('admin.forwarders.ledger') }}</h2>
              <NuxtLinkLocale :to="`/admin/finance?forwarder=${f.name}`" class="text-sm font-semibold text-sea hover:underline">{{ $t('common.viewAll') }}</NuxtLinkLocale>
            </div>
            <ul v-if="f.transactions.length" class="mt-3 divide-y divide-line">
              <li v-for="tx in f.transactions" :key="tx.name" class="flex items-center gap-3 py-2.5">
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm">{{ fmt.label('txn', tx.transaction_type) }}</p>
                  <p class="truncate text-xs text-faint">{{ fmt.date(tx.posting_date, 'short') }}<template v-if="tx.description"> · {{ tx.description }}</template></p>
                </div>
                <span class="text-sm font-semibold tabular-nums" :class="tx.amount > 0 ? 'text-success' : ''">{{ tx.amount > 0 ? '+' : '' }}{{ fmt.money(tx.amount, tx.currency) }}</span>
              </li>
            </ul>
            <p v-else class="mt-3 text-sm text-faint">{{ $t('wallet.emptyTitle') }}</p>
          </section>
        </div>
      </div>
    </template>

    <ConfirmDialog
      v-model="confirmOpen"
      :title="pending?.label || ''"
      :text="pending ? $t(`admin.forwarders.confirm.${pending.status}`, { name: f?.company_name }) : ''"
      :confirm-label="pending?.label || ''"
      :variant="pending?.variant"
      :reason="pending?.reason"
      :reason-hint="$t('admin.reasonShared')"
      :loading="busy === 'status'"
      @confirm="confirmStatus"
    />

    <AppModal v-model="adjustOpen" :title="$t('admin.forwarders.adjust')" size="sm">
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-2 rounded-xl bg-sunken p-1">
          <button v-for="d in (['credit', 'debit'] as const)" :key="d" type="button" class="rounded-lg py-2 text-sm font-semibold" :class="adjust.direction === d ? 'bg-surface text-ink shadow-sm' : 'text-muted'" @click="adjust.direction = d">
            {{ $t(`admin.forwarders.${d}`) }}
          </button>
        </div>
        <FormField v-model.number="adjust.amount" type="number" min="0.01" step="0.01" inputmode="decimal" :label="$t('wallet.amount')" :suffix="f?.wallet.currency" required />
        <FormField v-model="adjust.note" as="textarea" :label="$t('admin.forwarders.adjustNote')" :hint="$t('admin.forwarders.adjustHint')" required />
      </div>
      <template #footer>
        <AppButton variant="ghost" @click="adjustOpen = false">{{ $t('common.cancel') }}</AppButton>
        <AppButton :loading="busy === 'adjust'" :disabled="!adjust.amount || !adjust.note.trim()" @click="saveAdjust">{{ $t('admin.forwarders.post') }}</AppButton>
      </template>
    </AppModal>

    <AppModal v-model="editOpen" :title="$t('admin.forwarders.editCompany')">
      <div class="grid gap-4 sm:grid-cols-2">
        <FormField v-model="edit.company_name" class="sm:col-span-2" :label="$t('admin.forwarders.companyName')" required />
        <FormField v-model="edit.tagline" class="sm:col-span-2" :label="$t('admin.forwarders.tagline')" />
        <FormField v-model="edit.email" type="email" :label="$t('fields.email')" />
        <FormField v-model="edit.phone" type="tel" :label="$t('fields.phone')" />
        <FormField v-model="edit.website" class="sm:col-span-2" :label="$t('admin.forwarders.website')" />
        <FormField v-model="edit.city" :label="$t('fields.city')" />
        <CountrySelect v-model="edit.country" :label="$t('fields.country')" />
      </div>
      <template #footer>
        <AppButton variant="ghost" @click="editOpen = false">{{ $t('common.cancel') }}</AppButton>
        <AppButton :loading="busy === 'edit'" :disabled="!edit.company_name?.trim()" @click="saveEdit">{{ $t('common.saveChanges') }}</AppButton>
      </template>
    </AppModal>
  </div>
</template>
