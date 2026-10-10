<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'admin' })
const route = useRoute()
const { t } = useI18n()
const api = useSokan()
const fmt = useFormat()
const toast = useToast()
const errorMessage = useErrorMessage()
const countryLabel = useCountryLabel()
const id = computed(() => String(route.params.id))

const { data, status: loading, error } = await useAsyncData(`admin-req-${id.value}`, () => api.admin.request(id.value), { server: false })
const r = computed(() => data.value?.request)
useHead({ title: computed(() => r.value?.title || id.value) })

const cancelOpen = ref(false)
const cancelling = ref(false)
async function cancel(reason: string) {
  cancelling.value = true
  try {
    data.value = await api.admin.cancelRequest(id.value, reason)
    cancelOpen.value = false
    toast.success(t('admin.requests.cancelled'))
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    cancelling.value = false
  }
}

const facts = computed(() => {
  const v = r.value
  if (!v || !data.value) return []
  return [
    { label: t('admin.requests.customer'), value: data.value.customer_name },
    { label: t('admin.requests.mode'), value: v.mode?.name },
    { label: t('admin.requests.origin'), value: [v.origin?.city, countryLabel(v.origin?.country)].filter(Boolean).join(', ') },
    { label: t('admin.requests.destination'), value: [v.destination?.city, countryLabel(v.destination?.country)].filter(Boolean).join(', ') },
    { label: t('admin.requests.incoterm'), value: v.incoterm },
    { label: t('admin.requests.commodity'), value: v.commodity },
    { label: t('admin.requests.published'), value: data.value.published_on ? fmt.date(data.value.published_on) : null },
    { label: t('admin.requests.validUntil'), value: v.valid_until ? fmt.date(v.valid_until) : null },
    { label: t('admin.requests.contact'), value: [v.contact?.name, v.contact?.email, v.contact?.phone].filter(Boolean).join(' · ') },
    { label: t('admin.requests.booked'), value: data.value.booked_on ? fmt.date(data.value.booked_on) : null },
  ]
})
</script>

<template>
  <div>
    <PortalHeading :title="r?.title || ''" back="/admin/requests">
      <AppButton v-if="r && ['Draft', 'Open'].includes(r.status)" variant="danger" icon="ban" @click="cancelOpen = true">{{ $t('admin.requests.cancel') }}</AppButton>
    </PortalHeading>

    <div v-if="loading === 'pending' && !data" class="grid gap-4 lg:grid-cols-3"><div class="skeleton h-80 lg:col-span-2" /><div class="skeleton h-80" /></div>
    <div v-else-if="error" class="card"><EmptyState icon="alert" :title="$t('admin.notFound')" /></div>
    <template v-else-if="data && r">
      <div class="mb-6 flex flex-wrap items-center gap-3">
        <StatusPill :status="r.status" />
        <span class="font-mono text-xs text-faint">{{ r.name }}</span>
        <NuxtLinkLocale v-if="data.customer" :to="`/admin/customers/${data.customer}`" class="text-sm font-semibold text-sea hover:underline">{{ data.customer_name }}</NuxtLinkLocale>
      </div>
      <p v-if="data.cancel_reason" class="mb-6 rounded-2xl bg-danger/10 p-4 text-sm text-danger">{{ data.cancel_reason }}</p>

      <!-- Funnel for this request -->
      <div class="mb-4 grid grid-cols-3 gap-3">
        <div class="card p-4"><p class="font-display text-3xl tabular-nums">{{ fmt.number(data.leads_sent) }}</p><p class="text-xs text-muted">{{ $t('admin.requests.leadsSent') }}</p></div>
        <div class="card p-4"><p class="font-display text-3xl tabular-nums">{{ fmt.number(data.unlock_count) }}</p><p class="text-xs text-muted">{{ $t('admin.requests.unlocks') }}</p></div>
        <div class="card p-4"><p class="font-display text-3xl tabular-nums">{{ fmt.number(data.quotes.length) }}</p><p class="text-xs text-muted">{{ $t('admin.requests.quotes') }}</p></div>
      </div>

      <div class="grid gap-4 lg:grid-cols-3">
        <div class="space-y-4 lg:col-span-2">
          <section class="card p-5">
            <h2 class="mb-4 font-semibold">{{ $t('admin.requests.details') }}</h2>
            <Facts :items="facts" />
            <div class="mt-5 border-t border-line pt-4"><CargoChips :r="r" /></div>
            <p v-if="r.notes" class="mt-4 text-sm leading-relaxed whitespace-pre-line text-ink-soft">{{ r.notes }}</p>
          </section>

          <section class="card p-5">
            <h2 class="font-semibold">{{ $t('admin.requests.quotesTitle') }}</h2>
            <ul v-if="data.quotes.length" class="mt-3 divide-y divide-line">
              <li v-for="q in data.quotes" :key="q.name" class="flex flex-wrap items-center gap-3 py-3">
                <CompanyAvatar :name="q.forwarder.company_name" :logo="q.forwarder.logo" size="sm" />
                <div class="min-w-0 flex-1">
                  <NuxtLinkLocale :to="`/admin/forwarders/${q.forwarder.name}`" class="truncate text-sm font-semibold hover:text-sea">{{ q.forwarder.company_name }}</NuxtLinkLocale>
                  <p class="text-xs text-faint">
                    {{ $t('admin.requests.transit', { min: q.transit_days_min || '?', max: q.transit_days_max || '?' }) }} · {{ fmt.relative(q.creation) }}
                  </p>
                </div>
                <span class="font-semibold tabular-nums">{{ fmt.money(q.total_amount, q.currency) }}</span>
                <StatusPill :status="q.status" />
              </li>
            </ul>
            <p v-else class="mt-3 text-sm text-faint">{{ $t('admin.requests.noQuotes') }}</p>
          </section>
        </div>

        <div class="space-y-4">
          <section class="card p-5">
            <h2 class="font-semibold">{{ $t('admin.requests.leadsTitle') }}</h2>
            <ul v-if="data.leads.length" class="mt-3 divide-y divide-line">
              <li v-for="l in data.leads" :key="l.name" class="flex items-center gap-3 py-2.5">
                <div class="min-w-0 flex-1">
                  <NuxtLinkLocale :to="`/admin/forwarders/${l.forwarder}`" class="block truncate text-sm font-semibold hover:text-sea">{{ l.company_name }}</NuxtLinkLocale>
                  <p class="truncate text-xs text-faint">
                    <template v-if="l.unlocked_on">{{ l.was_free ? $t('admin.requests.unlockedFree') : $t('admin.requests.unlockedFee', { fee: fmt.money(l.unlock_fee, 'USD') }) }}</template>
                    <template v-else-if="l.seen_on">{{ $t('admin.requests.seen') }}</template>
                    <template v-else>{{ $t('admin.requests.notSeen') }}</template>
                  </p>
                </div>
                <StatusPill :status="l.status" group="leadStatus" />
              </li>
            </ul>
            <p v-else class="mt-3 text-sm text-faint">{{ $t('admin.requests.noLeads') }}</p>
          </section>

          <section v-if="data.review" class="card p-5">
            <div class="flex items-center justify-between gap-3">
              <h2 class="font-semibold">{{ $t('admin.nav.reviews') }}</h2>
              <StatusPill :status="data.review.status" />
            </div>
            <p class="mt-2 text-warning">{{ '★'.repeat(data.review.rating) }}<span class="text-line-strong">{{ '★'.repeat(5 - data.review.rating) }}</span></p>
            <p v-if="data.review.comment" class="mt-2 text-sm text-ink-soft">{{ data.review.comment }}</p>
            <NuxtLinkLocale to="/admin/reviews" class="mt-3 inline-block text-sm font-semibold text-sea hover:underline">{{ $t('admin.reviews.moderate') }}</NuxtLinkLocale>
          </section>
        </div>
      </div>
    </template>

    <ConfirmDialog
      v-model="cancelOpen"
      :title="$t('admin.requests.cancel')"
      :text="$t('admin.requests.cancelText')"
      :confirm-label="$t('admin.requests.cancel')"
      variant="danger"
      reason
      :reason-hint="$t('admin.reasonShared')"
      :loading="cancelling"
      @confirm="cancel"
    />
  </div>
</template>
