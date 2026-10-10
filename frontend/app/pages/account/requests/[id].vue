<script setup lang="ts">
import type { CustomerRequestDetail } from '~/types/sokan'

definePageMeta({ layout: 'portal', middleware: 'auth', role: 'customer' })
const route = useRoute()
const api = useSokan()
const fmt = useFormat()
const { t } = useI18n()
const toast = useToast()
const errorMessage = useErrorMessage()
const name = String(route.params.id)
useHead({ title: name })

const { data, status, refresh } = await useAsyncData(`cust-req-${name}`, () => api.customer.request(name), { server: false })
const r = computed(() => data.value?.request)

// New quotes arrive in real time via polling while the request is open.
const { pause, resume } = useIntervalFn(() => refresh(), 30000, { immediate: false })
watch(r, (v) => (v?.status === 'Open' ? resume() : pause()), { immediate: true })

const best = computed(() => {
  const live = (data.value?.quotes ?? []).filter((q) => q.status === 'Submitted')
  return live.length > 1 ? live.reduce((a, b) => (b.total_amount < a.total_amount ? b : a)).name : null
})
const fastest = computed(() => {
  const live = (data.value?.quotes ?? []).filter((q) => q.status === 'Submitted' && (q.transit_days_min || q.transit_days_max))
  if (live.length < 2) return null
  const days = (q: (typeof live)[number]) => q.transit_days_max || q.transit_days_min || 999
  return live.reduce((a, b) => (days(b) < days(a) ? b : a)).name
})

const busy = ref<string | null>(null)
async function run(key: string, fn: () => Promise<CustomerRequestDetail>, okText: string) {
  busy.value = key
  try {
    data.value = await fn()
    toast.success(okText)
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    busy.value = null
  }
}

const confirmAccept = ref<string | null>(null)
const cancelOpen = ref(false)
const cancelReason = ref('')
const rating = ref(0)
const comment = ref('')
watchEffect(() => {
  if (data.value?.review) {
    rating.value = data.value.review.rating
    comment.value = data.value.review.comment || ''
  }
})

async function sendReview() {
  busy.value = 'review'
  try {
    await api.customer.review(name, rating.value, comment.value)
    toast.success(t('requestDetail.reviewThanks'))
    await refresh()
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    busy.value = null
  }
}
</script>

<template>
  <div>
    <PortalHeading :title="r ? r.title : name" back="/account/requests">
      <StatusPill v-if="r" :status="r.status" />
    </PortalHeading>

    <div v-if="status === 'pending' && !data" class="space-y-4"><div class="skeleton h-40" /><div class="skeleton h-72" /></div>

    <div v-else-if="data && r" class="grid gap-6 lg:grid-cols-[1fr_340px]">
      <div class="space-y-6">
        <!-- Progress -->
        <div class="card p-5 sm:p-6">
          <RouteLine :origin="r.origin" :destination="r.destination" :icon="r.mode?.icon" size="lg" />
          <div v-if="r.status === 'Open'" class="mt-6 grid grid-cols-3 gap-3 text-center">
            <div class="rounded-xl bg-sunken p-3"><p class="text-xl font-bold">{{ fmt.number(data.leads_sent) }}</p><p class="text-xs text-muted">{{ $t('requestDetail.notified') }}</p></div>
            <div class="rounded-xl bg-sunken p-3"><p class="text-xl font-bold">{{ fmt.number(data.unlock_count) }}</p><p class="text-xs text-muted">{{ $t('requestDetail.reviewing') }}</p></div>
            <div class="rounded-xl bg-sea/10 p-3 text-sea"><p class="text-xl font-bold">{{ fmt.number(data.quotes.length) }}</p><p class="text-xs">{{ $t('requestDetail.quotes') }}</p></div>
          </div>
        </div>

        <!-- Quotes -->
        <section>
          <h2 class="mb-4 text-lg font-bold">{{ $t('requestDetail.quotesTitle') }}</h2>
          <div v-if="data.quotes.length" class="grid gap-4 xl:grid-cols-2">
            <QuoteCard
              v-for="q in data.quotes"
              :key="q.name"
              :q="q"
              :best="q.name === best"
              :fastest="q.name === fastest"
              :can-act="r.status === 'Open'"
              :busy="busy === q.name"
              @accept="confirmAccept = q.name"
              @reject="run(q.name, () => api.customer.reject(q.name), $t('requestDetail.rejected'))"
            />
          </div>
          <div v-else class="card">
            <EmptyState icon="clock" :title="$t('requestDetail.waitingTitle')" :text="r.status === 'Open' ? $t('requestDetail.waitingText') : $t('requestDetail.noQuotes')" />
          </div>
        </section>

        <!-- Review -->
        <section v-if="r.status === 'Booked'" class="card p-6">
          <h2 class="font-bold">{{ $t('requestDetail.reviewTitle') }}</h2>
          <p class="mt-1 text-sm text-muted">{{ $t('requestDetail.reviewText') }}</p>
          <RatingStars v-model="rating" :readonly="false" :size="30" class="mt-4" />
          <FormField v-model="comment" as="textarea" :rows="3" class="mt-4" :placeholder="$t('requestDetail.reviewPh')" />
          <AppButton class="mt-4" variant="primary" :disabled="!rating" :loading="busy === 'review'" @click="sendReview">{{ data.review ? $t('common.update') : $t('common.submit') }}</AppButton>
        </section>
      </div>

      <!-- Shipment details -->
      <aside class="space-y-4">
        <div class="card p-5">
          <h2 class="font-bold">{{ $t('requestDetail.shipment') }}</h2>
          <CargoChips class="mt-3" :r="r" />
          <dl class="mt-4 space-y-2.5 text-sm">
            <div class="flex justify-between gap-3"><dt class="text-muted">{{ $t('wizard.cargo.commodity') }}</dt><dd class="text-end font-semibold">{{ r.cargo.commodity }}</dd></div>
            <div class="flex justify-between gap-3"><dt class="text-muted">{{ $t('wizard.route.readyDate') }}</dt><dd class="font-semibold">{{ fmt.date(r.ready_date) }}</dd></div>
            <div v-if="r.valid_until" class="flex justify-between gap-3"><dt class="text-muted">{{ $t('requestDetail.deadline') }}</dt><dd class="font-semibold">{{ fmt.date(r.valid_until) }}</dd></div>
            <div v-if="r.cargo.chargeable_weight_kg" class="flex justify-between gap-3"><dt class="text-muted">{{ $t('wizard.chargeable') }}</dt><dd class="font-semibold">{{ fmt.weight(r.cargo.chargeable_weight_kg) }}</dd></div>
          </dl>
          <div class="mt-4 flex flex-wrap gap-1.5">
            <span v-for="(on, k) in r.services" v-show="on" :key="k" class="rounded-lg bg-success/10 px-2 py-1 text-xs font-semibold text-success">✓ {{ $t(`services.${k}`) }}</span>
          </div>
          <p v-if="r.notes" class="mt-4 rounded-xl bg-sunken p-3 text-sm text-ink-soft">{{ r.notes }}</p>
        </div>
        <div v-if="r.status === 'Draft'" class="card p-5">
          <p class="text-sm text-muted">{{ $t('requestDetail.draftText') }}</p>
          <AppButton class="mt-3" block variant="primary" :loading="busy === 'publish'" @click="run('publish', () => api.customer.publish(name), $t('requestDetail.published'))">{{ $t('requestDetail.publish') }}</AppButton>
        </div>
        <AppButton v-if="['Open', 'Draft'].includes(r.status)" block variant="danger" icon="ban" @click="cancelOpen = true">{{ $t('requestDetail.cancel') }}</AppButton>
        <p v-if="data.cancel_reason" class="text-sm text-muted">{{ $t('requestDetail.cancelReason') }}: {{ data.cancel_reason }}</p>
      </aside>
    </div>

    <AppModal :model-value="Boolean(confirmAccept)" :title="$t('requestDetail.confirmTitle')" size="sm" @update:model-value="confirmAccept = null">
      <p class="text-muted">{{ $t('requestDetail.confirmText') }}</p>
      <template #footer>
        <AppButton variant="ghost" @click="confirmAccept = null">{{ $t('common.cancel') }}</AppButton>
        <AppButton
          variant="primary"
          icon="check"
          :loading="busy === confirmAccept"
          @click="run(confirmAccept!, () => api.customer.accept(confirmAccept!), $t('requestDetail.bookedToast')).then(() => (confirmAccept = null))"
        >{{ $t('quotes.accept') }}</AppButton>
      </template>
    </AppModal>

    <AppModal v-model="cancelOpen" :title="$t('requestDetail.cancel')" size="sm">
      <FormField v-model="cancelReason" as="textarea" :rows="3" :label="$t('requestDetail.cancelWhy')" />
      <template #footer>
        <AppButton variant="ghost" @click="cancelOpen = false">{{ $t('common.back') }}</AppButton>
        <AppButton variant="danger" :loading="busy === 'cancel'" @click="run('cancel', () => api.customer.cancel(name, cancelReason), $t('requestDetail.cancelled')).then(() => (cancelOpen = false))">{{ $t('requestDetail.cancel') }}</AppButton>
      </template>
    </AppModal>
  </div>
</template>
