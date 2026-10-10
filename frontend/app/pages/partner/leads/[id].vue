<script setup lang="ts">
import type { LeadDetail, RequestFull } from '~/types/sokan'

/**
 * One lead, end to end: teaser → unlock (billed) → quote builder (billed on
 * first submit, free to revise) → outcome. The fee is always shown before
 * the click that incurs it.
 */
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'forwarder' })
const route = useRoute()
const api = useSokan()
const fmt = useFormat()
const { t } = useI18n()
const toast = useToast()
const errorMessage = useErrorMessage()
const { refresh: refreshMe } = useAuth()
const name = String(route.params.id)
useHead({ title: name })

const { data, status } = await useAsyncData(`lead-${name}`, () => api.partner.lead(name), { server: false })
const r = computed(() => data.value?.request)
const full = computed(() => (data.value?.lead.unlocked ? (data.value.request as RequestFull) : null))
const p = computed(() => data.value?.pricing)

const busy = ref('')
async function act(key: string, fn: () => Promise<LeadDetail>, ok?: string) {
  busy.value = key
  try {
    data.value = await fn()
    if (ok) toast.success(ok)
    refreshMe()
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    busy.value = ''
  }
}

// ---------------------------------------------------------------- quote builder

const GROUPS = ['Freight', 'Origin', 'Destination', 'Customs', 'Insurance', 'Surcharge', 'Other']
const BASES = ['Per Shipment', 'Per Container', 'Per KG', 'Per CBM', 'Per W/M', 'Per Package', 'Per Document']
const CURRENCIES = ['USD', 'EUR', 'GBP', 'CNY', 'AED', 'TRY', 'INR', 'IRR']
const inDays = (n: number) => new Date(Date.now() + n * 86400000).toISOString().slice(0, 10)

const quote = reactive({
  currency: 'USD',
  transit_days_min: null as number | null,
  transit_days_max: null as number | null,
  valid_until: inDays(7),
  carrier: '',
  routing: '',
  free_days: null as number | null,
  service_level: 'Standard',
  inclusions: '',
  exclusions: '',
  notes: '',
  charges: [{ charge_group: 'Freight', description: '', basis: 'Per Shipment', quantity: 1, unit_price: null as number | null }],
})

// Seed from an existing quote (revise) or sensible defaults for this request.
watch(
  data,
  (d) => {
    if (!d) return
    const q = d.my_quote
    if (q) {
      Object.assign(quote, {
        currency: q.currency,
        transit_days_min: q.transit_days_min,
        transit_days_max: q.transit_days_max,
        valid_until: q.valid_until,
        carrier: q.carrier || '',
        routing: q.routing || '',
        free_days: q.free_days,
        service_level: q.service_level || 'Standard',
        inclusions: q.inclusions || '',
        exclusions: q.exclusions || '',
        notes: q.notes || '',
        charges: q.charges.map((c) => ({ charge_group: c.group, description: c.description, basis: c.basis, quantity: c.quantity, unit_price: c.unit_price })),
      })
    } else {
      quote.currency = d.default_currency || 'USD'
      const first = quote.charges[0]
      if (first && !first.description) {
        const containers = d.request.cargo.containers
        first.description = t('quoteBuilder.mainFreight', { mode: d.request.mode ? t(`modes.${d.request.mode.code}.name`) : '' })
        if (containers.length) {
          first.basis = 'Per Container'
          first.quantity = containers.reduce((s, c) => s + c.qty, 0)
        }
      }
    }
  },
  { immediate: true },
)

const total = computed(() => quote.charges.reduce((s, c) => s + (Number(c.quantity) || 0) * (Number(c.unit_price) || 0), 0))

function addCharge(group = 'Origin') {
  quote.charges.push({ charge_group: group, description: '', basis: 'Per Shipment', quantity: 1, unit_price: null })
}

const QUICK = ['Origin', 'Destination', 'Customs', 'Insurance']

async function submitQuote() {
  if (!quote.charges.some((c) => c.description && Number(c.unit_price) > 0)) {
    toast.error(t('quoteBuilder.needCharge'))
    return
  }
  const payload = { ...quote, charges: quote.charges.filter((c) => c.description && Number(c.unit_price) > 0) }
  await act('quote', () => api.partner.quote(name, payload), data.value?.my_quote ? t('quoteBuilder.revised') : t('quoteBuilder.sent'))
}

const declineOpen = ref(false)
const declineReason = ref('')
async function decline() {
  busy.value = 'decline'
  try {
    await api.partner.decline(name, declineReason.value)
    toast.info(t('leads.declined'))
    await navigateTo(useLocalePath()('/partner/leads'))
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    busy.value = ''
  }
}
</script>

<template>
  <div>
    <PortalHeading :title="r ? r.title : name" back="/partner/leads">
      <StatusPill v-if="data" :status="data.lead.status" group="leadStatus" />
    </PortalHeading>

    <div v-if="status === 'pending' && !data" class="space-y-4"><div class="skeleton h-40" /><div class="skeleton h-80" /></div>

    <div v-else-if="data && r && p" class="grid gap-6 lg:grid-cols-[1fr_360px]">
      <div class="space-y-6">
        <!-- Won -->
        <Motion v-if="data.won" as="div" class="relative overflow-hidden rounded-3xl bg-success p-6 text-white" :initial="{ scale: 0.96, opacity: 0 }" :animate="{ scale: 1, opacity: 1 }">
          <p class="text-2xl font-extrabold">🎉 {{ $t('leads.wonTitle') }}</p>
          <p class="mt-1 text-white/85">{{ $t('leads.wonText') }}</p>
        </Motion>

        <div class="card p-5 sm:p-6">
          <RouteLine :origin="r.origin" :destination="r.destination" :icon="r.mode?.icon" size="lg" />
          <p class="mt-5 font-semibold">{{ r.cargo.commodity }}</p>
          <CargoChips class="mt-2" :r="r" />
          <dl class="mt-5 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div class="rounded-xl bg-sunken p-3"><dt class="text-xs text-faint">{{ $t('wizard.route.readyDate') }}</dt><dd class="font-bold">{{ fmt.date(r.ready_date, 'short') }}</dd></div>
            <div class="rounded-xl bg-sunken p-3"><dt class="text-xs text-faint">{{ $t('requestDetail.deadline') }}</dt><dd class="font-bold">{{ fmt.date(r.valid_until, 'short') }}</dd></div>
            <div class="rounded-xl bg-sunken p-3"><dt class="text-xs text-faint">{{ $t('wizard.chargeable') }}</dt><dd class="font-bold">{{ fmt.weight(r.cargo.chargeable_weight_kg) }}</dd></div>
            <div class="rounded-xl bg-sunken p-3"><dt class="text-xs text-faint">{{ $t('leads.quotesSoFar') }}</dt><dd class="font-bold">{{ fmt.number(data.competition.quotes) }}</dd></div>
          </dl>
          <div class="mt-4 flex flex-wrap gap-1.5">
            <span v-if="r.pickup_required" class="rounded-lg bg-brand/10 px-2 py-1 text-xs font-semibold text-brand">{{ $t('wizard.route.pickup') }}</span>
            <span v-if="r.delivery_required" class="rounded-lg bg-brand/10 px-2 py-1 text-xs font-semibold text-brand">{{ $t('wizard.route.delivery') }}</span>
            <span v-for="(on, k) in r.services" v-show="on" :key="k" class="rounded-lg bg-success/10 px-2 py-1 text-xs font-semibold text-success">{{ $t(`services.${k}`) }}</span>
          </div>
        </div>

        <!-- Locked / unlocked details -->
        <div v-if="!full" class="relative overflow-hidden rounded-3xl border border-line bg-surface">
          <div class="pointer-events-none space-y-3 p-6 blur-[6px] select-none" aria-hidden="true">
            <div class="h-4 w-2/3 rounded bg-sunken" /><div class="h-4 w-1/2 rounded bg-sunken" /><div class="h-4 w-3/4 rounded bg-sunken" /><div class="h-20 rounded-xl bg-sunken" />
          </div>
          <div class="absolute inset-0 grid place-items-center bg-surface/60 p-6 text-center backdrop-blur-[2px]">
            <div class="max-w-sm">
              <span class="mx-auto grid size-14 place-items-center rounded-2xl bg-brand-gradient text-white shadow-lg shadow-brand/30"><AppIcon name="lock" :size="24" /></span>
              <h2 class="mt-4 text-lg font-bold">{{ $t('leads.lockedTitle') }}</h2>
              <p class="mt-1 text-sm text-muted">{{ $t('leads.lockedText') }}</p>
            </div>
          </div>
        </div>
        <div v-else class="card p-5 sm:p-6">
          <h2 class="font-bold">{{ $t('leads.details') }}</h2>
          <div class="mt-4 grid gap-4 sm:grid-cols-2">
            <div class="rounded-xl bg-brand/6 p-4 ring-1 ring-brand/15">
              <p class="text-xs font-semibold text-brand">{{ $t('leads.customer') }}</p>
              <p class="mt-1 font-bold">{{ full.contact.name }}</p>
              <p v-if="full.contact.company" class="text-sm text-muted">{{ full.contact.company }}</p>
              <p class="mt-2 space-y-1 text-sm">
                <a v-if="full.contact.email" :href="`mailto:${full.contact.email}`" class="flex items-center gap-1.5 font-semibold text-brand" dir="ltr"><AppIcon name="mail" :size="14" /> {{ full.contact.email }}</a>
                <a v-if="full.contact.phone" :href="`tel:${full.contact.phone}`" class="flex items-center gap-1.5 font-semibold text-brand" dir="ltr"><AppIcon name="phone" :size="14" /> {{ full.contact.phone }}</a>
              </p>
            </div>
            <dl class="space-y-2 text-sm">
              <div v-if="full.origin.port" class="flex justify-between gap-2"><dt class="text-muted">{{ $t('leads.pol') }}</dt><dd class="font-semibold">{{ full.origin.port }}</dd></div>
              <div v-if="full.destination.port" class="flex justify-between gap-2"><dt class="text-muted">{{ $t('leads.pod') }}</dt><dd class="font-semibold">{{ full.destination.port }}</dd></div>
              <div v-if="full.hs_code" class="flex justify-between gap-2"><dt class="text-muted">{{ $t('wizard.cargo.hs') }}</dt><dd class="font-semibold">{{ full.hs_code }}</dd></div>
              <div v-if="full.un_number" class="flex justify-between gap-2"><dt class="text-muted">{{ $t('wizard.cargo.un') }}</dt><dd class="font-semibold">{{ full.un_number }}</dd></div>
              <div v-if="full.temperature_range" class="flex justify-between gap-2"><dt class="text-muted">{{ $t('wizard.cargo.temp') }}</dt><dd class="font-semibold">{{ full.temperature_range }}</dd></div>
              <div v-if="full.cargo_value" class="flex justify-between gap-2"><dt class="text-muted">{{ $t('wizard.cargo.value') }}</dt><dd class="font-semibold">{{ fmt.money(full.cargo_value, full.cargo_currency || 'USD') }}</dd></div>
              <div class="flex justify-between gap-2"><dt class="text-muted">{{ $t('wizard.cargo.stackable') }}</dt><dd class="font-semibold">{{ full.cargo.is_stackable ? $t('common.yes') : $t('common.no') }}</dd></div>
            </dl>
          </div>
          <div v-if="full.pickup_address || full.delivery_address" class="mt-4 grid gap-3 sm:grid-cols-2 text-sm">
            <p v-if="full.pickup_address" class="rounded-xl bg-sunken p-3"><b>{{ $t('wizard.route.pickupAddress') }}:</b> {{ full.pickup_address }}</p>
            <p v-if="full.delivery_address" class="rounded-xl bg-sunken p-3"><b>{{ $t('wizard.route.deliveryAddress') }}:</b> {{ full.delivery_address }}</p>
          </div>
          <div v-if="full.packages.length" class="mt-5 overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="text-xs text-faint"><tr class="border-b border-line"><th class="py-2 text-start">{{ $t('wizard.cargo.type') }}</th><th class="text-end">{{ $t('wizard.cargo.qty') }}</th><th class="text-end">L×W×H</th><th class="text-end">{{ $t('units.kg') }}</th><th class="text-end">{{ $t('units.cbm') }}</th></tr></thead>
              <tbody>
                <tr v-for="(pk, i) in full.packages" :key="i" class="border-b border-line last:border-0">
                  <td class="py-2">{{ fmt.label('packages', pk.type) }}</td><td class="text-end">{{ pk.qty }}</td><td class="text-end" dir="ltr">{{ pk.length_cm }}×{{ pk.width_cm }}×{{ pk.height_cm }}</td><td class="text-end">{{ pk.weight_kg }}</td><td class="text-end">{{ fmt.number(pk.volume_cbm, 3) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="full.notes" class="mt-4 rounded-xl bg-sunken p-3 text-sm">{{ full.notes }}</p>
          <a v-if="full.attachment" :href="full.attachment" target="_blank" class="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-brand"><AppIcon name="file-text" :size="16" /> {{ $t('leads.attachment') }}</a>
        </div>

        <!-- Quote builder -->
        <section v-if="full && r.status === 'Open' && (!data.my_quote || data.my_quote.status === 'Submitted')" class="card p-5 sm:p-6">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <h2 class="text-lg font-bold">{{ data.my_quote ? $t('quoteBuilder.reviseTitle') : $t('quoteBuilder.title') }}</h2>
            <FormField v-model="quote.currency" as="select" class="w-28">
              <template #options><option v-for="c in CURRENCIES" :key="c" :value="c">{{ c }}</option></template>
            </FormField>
          </div>

          <TransitionGroup tag="div" class="mt-5 space-y-3" enter-active-class="transition duration-300" enter-from-class="opacity-0 -translate-y-2" leave-active-class="transition duration-200" leave-to-class="opacity-0">
            <div v-for="(c, i) in quote.charges" :key="i" class="grid grid-cols-2 gap-2 rounded-xl bg-sunken p-3 sm:grid-cols-[1fr_2fr_1.2fr_0.7fr_1fr_auto] sm:items-end">
              <FormField v-model="c.charge_group" as="select" :label="i === 0 ? $t('quoteBuilder.group') : undefined">
                <template #options><option v-for="g in GROUPS" :key="g" :value="g">{{ fmt.label('chargeGroups', g) }}</option></template>
              </FormField>
              <FormField v-model="c.description" :label="i === 0 ? $t('quoteBuilder.description') : undefined" :placeholder="$t('quoteBuilder.descriptionPh')" />
              <FormField v-model="c.basis" as="select" :label="i === 0 ? $t('quoteBuilder.basis') : undefined">
                <template #options><option v-for="b in BASES" :key="b" :value="b">{{ fmt.label('bases', b) }}</option></template>
              </FormField>
              <FormField v-model.number="c.quantity" type="number" min="0" step="any" inputmode="decimal" :label="i === 0 ? $t('wizard.cargo.qty') : undefined" />
              <FormField v-model.number="c.unit_price" type="number" min="0" step="any" inputmode="decimal" :label="i === 0 ? $t('quoteBuilder.price') : undefined" />
              <button type="button" class="grid size-10 place-items-center self-end rounded-lg text-faint hover:bg-danger/10 hover:text-danger disabled:opacity-30" :disabled="quote.charges.length === 1" :aria-label="$t('common.remove')" @click="quote.charges.splice(i, 1)">
                <AppIcon name="trash" :size="18" />
              </button>
            </div>
          </TransitionGroup>
          <div class="mt-3 flex flex-wrap gap-2">
            <AppButton size="sm" variant="ghost" icon="plus" @click="addCharge('Other')">{{ $t('quoteBuilder.addLine') }}</AppButton>
            <button v-for="g in QUICK" :key="g" type="button" class="rounded-lg bg-sunken px-3 py-1.5 text-xs font-semibold text-ink-soft hover:bg-brand/10 hover:text-brand" @click="addCharge(g)">+ {{ fmt.label('chargeGroups', g) }}</button>
          </div>

          <div class="mt-6 grid gap-4 sm:grid-cols-3">
            <FormField v-model.number="quote.transit_days_min" type="number" min="0" inputmode="numeric" :label="$t('quoteBuilder.transitMin')" :suffix="$t('units.days')" />
            <FormField v-model.number="quote.transit_days_max" type="number" min="0" inputmode="numeric" :label="$t('quoteBuilder.transitMax')" :suffix="$t('units.days')" />
            <FormField v-model="quote.valid_until" type="date" :min="inDays(0)" :label="$t('quotes.validUntil')" required />
            <FormField v-model="quote.carrier" :label="$t('quotes.carrier')" />
            <FormField v-model="quote.routing" :label="$t('quotes.routing')" :placeholder="$t('quoteBuilder.routingPh')" />
            <FormField v-model.number="quote.free_days" type="number" min="0" inputmode="numeric" :label="$t('quotes.freeDays')" />
          </div>
          <div class="mt-4 grid gap-4 sm:grid-cols-2">
            <FormField v-model="quote.inclusions" as="textarea" :rows="2" :label="$t('quotes.included')" />
            <FormField v-model="quote.exclusions" as="textarea" :rows="2" :label="$t('quotes.excluded')" />
          </div>
          <FormField v-model="quote.notes" as="textarea" :rows="3" class="mt-4" :label="$t('quoteBuilder.notes')" />

          <div class="mt-6 flex flex-col gap-4 rounded-2xl bg-night-950 p-5 text-white sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p class="text-sm text-white/60">{{ $t('quoteBuilder.total') }}</p>
              <p class="text-3xl font-black tabular-nums">{{ fmt.money(total, quote.currency) }}</p>
              <p v-if="!data.my_quote" class="mt-1 text-xs text-white/60">
                {{ p.quote_fee ? $t('quoteBuilder.feeNote', { fee: fmt.money(p.quote_fee, p.currency) }) : $t('quoteBuilder.freeNote', { n: fmt.number(p.free_quotes_left) }) }}
              </p>
              <p v-else class="mt-1 text-xs text-white/60">{{ $t('quoteBuilder.reviseFree') }}</p>
            </div>
            <AppButton variant="accent" size="lg" icon-end="send" :loading="busy === 'quote'" @click="submitQuote">{{ data.my_quote ? $t('quoteBuilder.update') : $t('quoteBuilder.send') }}</AppButton>
          </div>
        </section>

        <!-- Submitted quote (read-only when not editable) -->
        <section v-else-if="data.my_quote" class="card p-5 sm:p-6">
          <div class="flex items-center justify-between">
            <h2 class="font-bold">{{ $t('quoteBuilder.yourQuote') }}</h2>
            <StatusPill :status="data.my_quote.status" />
          </div>
          <p class="mt-3 text-3xl font-black">{{ fmt.money(data.my_quote.total_amount, data.my_quote.currency) }}</p>
        </section>
      </div>

      <!-- Action rail -->
      <aside class="space-y-4">
        <div class="sticky top-24 space-y-4">
          <div v-if="!data.lead.unlocked && r.status === 'Open'" class="overflow-hidden rounded-3xl bg-night-950 p-6 text-white">
            <p class="text-sm text-white/60">{{ $t('leads.unlockCost') }}</p>
            <p class="mt-1 text-4xl font-black">{{ p.unlock_fee ? fmt.money(p.unlock_fee, p.currency) : $t('pricing.free') }}</p>
            <p class="mt-1 text-xs text-white/60">
              {{ p.free_views_left ? $t('leads.freeLeft', { n: fmt.number(p.free_views_left) }) : $t('leads.balance', { b: fmt.money(p.balance, p.currency) }) }}
            </p>
            <ul class="mt-5 space-y-2 text-sm text-white/80">
              <li v-for="k in ['u1', 'u2', 'u3']" :key="k" class="flex gap-2"><AppIcon name="check" :size="16" class="mt-0.5 shrink-0 text-lagoon" />{{ $t(`leads.${k}`) }}</li>
            </ul>
            <AppButton class="mt-6" block variant="accent" size="lg" icon="lock-open" :loading="busy === 'unlock'" @click="act('unlock', () => api.partner.unlock(name), $t('leads.unlocked'))">
              {{ $t('leads.unlock') }}
            </AppButton>
            <p v-if="p.unlock_fee && p.balance < p.unlock_fee" class="mt-3 text-center text-xs text-coral">
              {{ $t('leads.needTopUp') }} <NuxtLinkLocale to="/partner/wallet" class="font-bold underline">{{ $t('portal.topUp') }}</NuxtLinkLocale>
            </p>
          </div>

          <div v-else-if="r.status !== 'Open'" class="card p-5 text-sm text-muted">{{ $t('leads.closed', { status: fmt.label('status', r.status) }) }}</div>

          <div v-if="data.lead.unlocked" class="card p-5 text-sm">
            <p class="font-semibold">{{ $t('leads.unlockedOn', { date: fmt.date(data.lead.unlocked_on) }) }}</p>
            <p class="mt-1 text-muted">{{ data.lead.was_free ? $t('leads.wasFree') : $t('leads.charged', { fee: fmt.money(data.lead.unlock_fee, p.currency) }) }}</p>
          </div>

          <AppButton
            v-if="data.my_quote?.status === 'Submitted'"
            block
            variant="ghost"
            icon="undo"
            :loading="busy === 'withdraw'"
            @click="act('withdraw', () => api.partner.withdraw(name), $t('quoteBuilder.withdrawn'))"
          >{{ $t('quoteBuilder.withdraw') }}</AppButton>
          <AppButton v-if="!data.my_quote && r.status === 'Open' && data.lead.status !== 'Declined'" block variant="ghost" icon="ban" @click="declineOpen = true">{{ $t('leads.decline') }}</AppButton>
        </div>
      </aside>
    </div>

    <AppModal v-model="declineOpen" :title="$t('leads.decline')" size="sm">
      <p class="mb-4 text-sm text-muted">{{ $t('leads.declineText') }}</p>
      <FormField v-model="declineReason" as="select">
        <template #options>
          <option value="">{{ $t('leads.reason.none') }}</option>
          <option v-for="k in ['lane', 'capacity', 'cargo', 'timing']" :key="k" :value="$t(`leads.reason.${k}`)">{{ $t(`leads.reason.${k}`) }}</option>
        </template>
      </FormField>
      <template #footer>
        <AppButton variant="ghost" @click="declineOpen = false">{{ $t('common.back') }}</AppButton>
        <AppButton variant="danger" :loading="busy === 'decline'" @click="decline">{{ $t('leads.decline') }}</AppButton>
      </template>
    </AppModal>
  </div>
</template>
