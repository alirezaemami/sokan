<script setup lang="ts">
import type { TransportMode } from '~/types/sokan'

/**
 * Four-step freight request. The draft persists in localStorage so a visitor
 * who wanders off (or signs in mid-way) comes back to their answers. Guests
 * create an account on the last step instead of being bounced to a sign-up
 * page first — the request is the reason they came.
 */
const props = defineProps<{ modes: TransportMode[] }>()

const { t } = useI18n()
const fmt = useFormat()
const route = useRoute()
const api = useSokan()
const toast = useToast()
const errorMessage = useErrorMessage()
const { me, isLoggedIn, isCustomer, setMe, login, refresh } = useAuth()

const CONTAINERS = ["20' Standard", "40' Standard", "40' High Cube", "45' High Cube", "20' Reefer", "40' Reefer", "20' Open Top", "40' Open Top", "20' Flat Rack", "40' Flat Rack", "20' Tank"]
const PACKAGES = ['Pallet', 'Carton', 'Crate', 'Drum', 'Bag', 'Bundle', 'Roll', 'Loose', 'Other']
const CATEGORIES = ['General Cargo', 'Dangerous Goods', 'Temperature Controlled', 'Oversized / Heavy Lift', 'Fragile', 'Perishable', 'Vehicles', 'High Value']
const INCOTERMS = ['EXW', 'FCA', 'FAS', 'FOB', 'CFR', 'CIF', 'CPT', 'CIP', 'DAP', 'DPU', 'DDP']
const CURRENCIES = ['USD', 'EUR', 'GBP', 'CNY', 'AED', 'TRY', 'INR', 'IRR']
const VOLUMETRIC: Record<string, number> = { Air: 167, Courier: 200, Road: 333, Rail: 333 }

const inDays = (n: number) => new Date(Date.now() + n * 86400000).toISOString().slice(0, 10)

function blank() {
  return {
    transport_mode: '',
    incoterm: '',
    origin_country: null as string | null,
    origin_city: '',
    origin_port: '',
    pickup_required: false,
    pickup_address: '',
    destination_country: null as string | null,
    destination_city: '',
    destination_port: '',
    delivery_required: false,
    delivery_address: '',
    ready_date: inDays(3),
    valid_until: '',
    commodity: '',
    hs_code: '',
    cargo_category: 'General Cargo',
    is_stackable: true,
    un_number: '',
    temperature_range: '',
    cargo_value: null as number | null,
    cargo_currency: 'USD',
    totals_only: false,
    total_weight_kg: null as number | null,
    total_volume_cbm: null as number | null,
    containers: [{ container_type: "40' High Cube", quantity: 1, weight_kg: null as number | null }],
    packages: [{ package_type: 'Pallet', quantity: 1, length_cm: 120, width_cm: 80, height_cm: 100, weight_kg: null as number | null }],
    need_customs_clearance: false,
    need_insurance: false,
    need_warehousing: false,
    need_packing: false,
    quote_currency: 'USD',
    notes: '',
  }
}

const draft = useLocalStorage('sokan-request-draft', blank(), { mergeDefaults: true })
const form = reactive(draft.value)
watch(form, (v) => (draft.value = { ...v }), { deep: true })

const step = ref(0)
const direction = ref(1)
const STEPS = ['route', 'cargo', 'services', 'review'] as const
const errors = reactive<Record<string, string>>({})

// Prefill from the home-page quick start / mode tiles.
onMounted(() => {
  const q = route.query
  if (q.mode && props.modes.some((m) => m.name === q.mode)) form.transport_mode = String(q.mode)
  if (q.from) form.origin_country = String(q.from)
  if (q.to) form.destination_country = String(q.to)
  if (form.ready_date < inDays(0)) form.ready_date = inDays(3)
})
watchEffect(() => {
  if (!form.transport_mode && props.modes.length) form.transport_mode = props.modes[0]!.name
})

const mode = computed(() => props.modes.find((m) => m.name === form.transport_mode))
const usesContainers = computed(() => Boolean(mode.value?.uses_containers))

const totals = computed(() => {
  if (usesContainers.value) {
    const weight = form.containers.reduce((s, c) => s + (Number(c.weight_kg) || 0) * (Number(c.quantity) || 0), 0)
    return { weight, volume: 0, count: form.containers.reduce((s, c) => s + (Number(c.quantity) || 0), 0) }
  }
  if (form.totals_only) return { weight: Number(form.total_weight_kg) || 0, volume: Number(form.total_volume_cbm) || 0, count: 0 }
  let weight = 0
  let volume = 0
  let count = 0
  for (const p of form.packages) {
    const q = Number(p.quantity) || 0
    count += q
    weight += (Number(p.weight_kg) || 0) * q
    volume += ((Number(p.length_cm) || 0) * (Number(p.width_cm) || 0) * (Number(p.height_cm) || 0) * q) / 1e6
  }
  return { weight, volume, count }
})

const chargeable = computed(() => {
  const divisor = VOLUMETRIC[mode.value?.category || ''] ?? 1000
  return Math.max(totals.value.weight, totals.value.volume * divisor)
})

// ---------------------------------------------------------------- validation

function validate(i: number) {
  Object.keys(errors).forEach((k) => delete errors[k])
  const req = (field: keyof typeof form, ok = Boolean(form[field])) => {
    if (!ok) errors[field] = t('wizard.required')
  }
  if (i === 0) {
    req('transport_mode')
    req('origin_country')
    req('origin_city', Boolean(form.origin_city.trim()))
    req('destination_country')
    req('destination_city', Boolean(form.destination_city.trim()))
    req('ready_date')
    if (form.origin_country && form.origin_country === form.destination_country && form.origin_city.trim().toLowerCase() === form.destination_city.trim().toLowerCase()) {
      errors.destination_city = t('wizard.sameplace')
    }
  }
  if (i === 1) {
    req('commodity', Boolean(form.commodity.trim()))
    if (usesContainers.value && !form.containers.some((c) => Number(c.quantity) > 0)) errors.containers = t('wizard.addContainer')
    if (!usesContainers.value && totals.value.weight <= 0) errors.weight = t('wizard.addWeight')
  }
  if (i === 3 && !isLoggedIn.value) {
    if (account.mode === 'register') {
      if (!account.full_name.trim()) errors.full_name = t('wizard.required')
      if (!/^\S+@\S+\.\S+$/.test(account.email)) errors.email = t('auth.invalidEmail')
      if (account.password.length < 8) errors.password = t('auth.passwordShort')
    } else {
      if (!account.email) errors.email = t('wizard.required')
      if (!account.password) errors.password = t('wizard.required')
    }
  }
  return Object.keys(errors).length === 0
}

function next() {
  if (!validate(step.value)) {
    toast.error(t('wizard.fixErrors'))
    return
  }
  direction.value = 1
  step.value = Math.min(step.value + 1, STEPS.length - 1)
  scrollTop()
}

function back() {
  direction.value = -1
  step.value = Math.max(step.value - 1, 0)
  scrollTop()
}

function goto(i: number) {
  if (i < step.value) {
    direction.value = -1
    step.value = i
    scrollTop()
  }
}

function scrollTop() {
  if (import.meta.client) window.scrollTo({ top: 0, behavior: 'smooth' })
}

// ---------------------------------------------------------------- account + submit

const account = reactive({ mode: 'register' as 'register' | 'login', full_name: '', email: '', phone: '', company_name: '', password: '' })
const file = ref<File | null>(null)
const submitting = ref(false)
const result = ref<{ name: string; status: string; leads_sent: number } | null>(null)

async function ensureCustomer() {
  if (!isLoggedIn.value) {
    if (account.mode === 'register') {
      setMe(
        await api.registerCustomer({
          full_name: account.full_name,
          email: account.email,
          password: account.password,
          phone: account.phone,
          company_name: account.company_name,
          country: form.origin_country,
        }),
      )
    } else {
      await login(account.email, account.password)
    }
  }
  if (!isCustomer.value) setMe(await api.becomeCustomer({ phone: account.phone || undefined }))
}

async function submit() {
  if (!validate(3)) return
  submitting.value = true
  try {
    await ensureCustomer()
    let attachment: string | undefined
    if (file.value) attachment = await uploadFile(file.value, { isPrivate: true, csrf: me.value?.csrf_token })

    const { totals_only, containers, packages, ...rest } = form
    const payload: Record<string, unknown> = { ...rest, attachment }
    if (usesContainers.value) payload.containers = containers.filter((c) => Number(c.quantity) > 0)
    else if (totals_only) Object.assign(payload, { total_weight_kg: form.total_weight_kg, total_volume_cbm: form.total_volume_cbm })
    else payload.packages = packages.filter((p) => Number(p.quantity) > 0)
    if (!payload.valid_until) delete payload.valid_until

    result.value = await api.customer.create(payload)
    draft.value = blank()
    Object.assign(form, blank())
    scrollTop()
  } catch (e) {
    toast.error(errorMessage(e))
    await refresh()
  } finally {
    submitting.value = false
  }
}

function addContainer() {
  form.containers.push({ container_type: "40' Standard", quantity: 1, weight_kg: null })
}
function addPackage() {
  form.packages.push({ package_type: 'Pallet', quantity: 1, length_cm: 120, width_cm: 80, height_cm: 100, weight_kg: null })
}
function onFile(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f && f.size > 10 * 1024 * 1024) {
    toast.error(t('wizard.fileTooBig'))
    return
  }
  file.value = f ?? null
}
</script>

<template>
  <!-- Success -->
  <div v-if="result" class="mx-auto max-w-xl py-10 text-center">
    <Motion
      as="div"
      class="relative mx-auto grid size-24 place-items-center rounded-full bg-success text-white shadow-2xl shadow-success/40"
      :initial="{ scale: 0, rotate: -90 }"
      :animate="{ scale: 1, rotate: 0 }"
      :transition="{ type: 'spring', stiffness: 260, damping: 16 }"
    >
      <span class="animate-ping-slow absolute inset-0 rounded-full bg-success/40" />
      <AppIcon name="check" :size="44" :stroke-width="3" />
    </Motion>
    <Motion as="div" :initial="{ opacity: 0, y: 16 }" :animate="{ opacity: 1, y: 0 }" :transition="{ delay: 0.25 }">
      <h2 class="mt-8 text-3xl font-extrabold">{{ result.status === 'Open' ? $t('wizard.successTitle') : $t('wizard.reviewTitle') }}</h2>
      <p class="mt-3 text-lg text-muted">
        {{ result.status === 'Open' ? $t('wizard.successText', { n: fmt.number(result.leads_sent || 0) }) : $t('wizard.reviewText') }}
      </p>
      <p class="mt-2 text-sm text-faint">{{ $t('wizard.reference', { ref: result.name }) }}</p>
      <div class="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
        <AppButton :to="`/account/requests/${result.name}`" variant="primary" size="lg" icon-end="arrow-right">{{ $t('wizard.track') }}</AppButton>
        <AppButton variant="secondary" size="lg" icon="plus" @click="result = null; step = 0">{{ $t('wizard.another') }}</AppButton>
      </div>
    </Motion>
  </div>

  <div v-else class="grid gap-8 lg:grid-cols-[1fr_320px]">
    <div class="min-w-0">
      <!-- Stepper -->
      <ol class="mb-8 grid grid-cols-4 gap-2">
        <li v-for="(s, i) in STEPS" :key="s">
          <button type="button" class="group w-full text-start" :disabled="i > step" @click="goto(i)">
            <span class="block h-1.5 overflow-hidden rounded-full bg-line-strong">
              <span class="block h-full rounded-full bg-brand-gradient transition-all duration-700 ease-[var(--ease-spring)]" :style="{ width: i < step ? '100%' : i === step ? '50%' : '0%' }" />
            </span>
            <span class="mt-2 hidden text-xs font-semibold sm:block" :class="i <= step ? 'text-ink' : 'text-faint'">{{ i + 1 }}. {{ $t(`wizard.steps.${s}`) }}</span>
          </button>
        </li>
      </ol>
      <p class="mb-6 text-sm font-semibold text-brand sm:hidden">{{ $t('wizard.stepOf', { n: step + 1, total: STEPS.length }) }} · {{ $t(`wizard.steps.${STEPS[step]}`) }}</p>

      <AnimatePresence mode="wait" :custom="direction">
        <Motion
          :key="step"
          as="div"
          :initial="{ opacity: 0, x: 40 * direction }"
          :animate="{ opacity: 1, x: 0 }"
          :exit="{ opacity: 0, x: -40 * direction }"
          :transition="{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }"
        >
          <!-- STEP 1: route -->
          <div v-if="step === 0" class="space-y-6">
            <div>
              <h2 class="text-2xl font-extrabold">{{ $t('wizard.route.title') }}</h2>
              <p class="mt-1 text-muted">{{ $t('wizard.route.subtitle') }}</p>
            </div>
            <div class="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
              <button
                v-for="m in modes"
                :key="m.name"
                type="button"
                class="flex flex-col items-start gap-2 rounded-2xl border-2 p-4 text-start transition-all duration-300"
                :class="form.transport_mode === m.name ? 'border-brand bg-brand/8 shadow-lg shadow-brand/10' : 'border-line bg-surface hover:border-brand/30'"
                @click="form.transport_mode = m.name"
              >
                <span class="grid size-10 place-items-center rounded-xl transition-colors" :class="form.transport_mode === m.name ? 'bg-brand-gradient text-white' : 'bg-sunken text-ink-soft'">
                  <AppIcon :name="m.icon" :size="20" />
                </span>
                <span class="text-sm font-bold">{{ $t(`modes.${m.code}.name`) }}</span>
              </button>
            </div>

            <div class="grid gap-5 md:grid-cols-2">
              <fieldset class="card space-y-4 p-5">
                <legend class="sr-only">{{ $t('wizard.route.origin') }}</legend>
                <p class="flex items-center gap-2 font-bold"><span class="size-2.5 rounded-full bg-brand" /> {{ $t('wizard.route.origin') }}</p>
                <CountrySelect v-model="form.origin_country" :label="$t('fields.country')" required :error="errors.origin_country" />
                <FormField v-model="form.origin_city" :label="$t('fields.city')" required :error="errors.origin_city" icon="map-pin" />
                <FormField v-model="form.origin_port" :label="$t('wizard.route.port')" :hint="$t('common.optional')" />
                <label class="flex items-center gap-3 text-sm font-semibold"><input v-model="form.pickup_required" type="checkbox" class="size-5 accent-brand" /> {{ $t('wizard.route.pickup') }}</label>
                <FormField v-if="form.pickup_required" v-model="form.pickup_address" as="textarea" :rows="2" :label="$t('wizard.route.pickupAddress')" />
              </fieldset>
              <fieldset class="card space-y-4 p-5">
                <legend class="sr-only">{{ $t('wizard.route.destination') }}</legend>
                <p class="flex items-center gap-2 font-bold"><span class="size-2.5 rounded-full bg-lagoon" /> {{ $t('wizard.route.destination') }}</p>
                <CountrySelect v-model="form.destination_country" :label="$t('fields.country')" required :error="errors.destination_country" />
                <FormField v-model="form.destination_city" :label="$t('fields.city')" required :error="errors.destination_city" icon="map-pin" />
                <FormField v-model="form.destination_port" :label="$t('wizard.route.port')" :hint="$t('common.optional')" />
                <label class="flex items-center gap-3 text-sm font-semibold"><input v-model="form.delivery_required" type="checkbox" class="size-5 accent-brand" /> {{ $t('wizard.route.delivery') }}</label>
                <FormField v-if="form.delivery_required" v-model="form.delivery_address" as="textarea" :rows="2" :label="$t('wizard.route.deliveryAddress')" />
              </fieldset>
            </div>

            <div class="grid gap-5 sm:grid-cols-2">
              <FormField v-model="form.ready_date" type="date" :min="inDays(0)" :label="$t('wizard.route.readyDate')" required :error="errors.ready_date" />
              <FormField v-model="form.incoterm" as="select" :label="$t('wizard.route.incoterm')" :hint="$t('wizard.route.incotermHint')">
                <template #options>
                  <option value="">{{ $t('wizard.route.notSure') }}</option>
                  <option v-for="i in INCOTERMS" :key="i" :value="i">{{ i }}</option>
                </template>
              </FormField>
            </div>
          </div>

          <!-- STEP 2: cargo -->
          <div v-else-if="step === 1" class="space-y-6">
            <div>
              <h2 class="text-2xl font-extrabold">{{ $t('wizard.cargo.title') }}</h2>
              <p class="mt-1 text-muted">{{ $t('wizard.cargo.subtitle') }}</p>
            </div>
            <div class="grid gap-5 sm:grid-cols-2">
              <FormField v-model="form.commodity" :label="$t('wizard.cargo.commodity')" :placeholder="$t('wizard.cargo.commodityPh')" required :error="errors.commodity" class="sm:col-span-2" />
              <FormField v-model="form.cargo_category" as="select" :label="$t('wizard.cargo.category')">
                <template #options>
                  <option v-for="c in CATEGORIES" :key="c" :value="c">{{ fmt.label('categories', c) }}</option>
                </template>
              </FormField>
              <FormField v-model="form.hs_code" :label="$t('wizard.cargo.hs')" :hint="$t('common.optional')" dir="ltr" />
              <FormField v-if="form.cargo_category === 'Dangerous Goods'" v-model="form.un_number" :label="$t('wizard.cargo.un')" dir="ltr" />
              <FormField v-if="form.cargo_category === 'Temperature Controlled'" v-model="form.temperature_range" :label="$t('wizard.cargo.temp')" placeholder="+2 / +8 °C" />
            </div>

            <!-- Containers -->
            <div v-if="usesContainers" class="card p-5">
              <div class="flex items-center justify-between">
                <h3 class="font-bold">{{ $t('wizard.cargo.containers') }}</h3>
                <AppButton size="sm" variant="ghost" icon="plus" @click="addContainer">{{ $t('common.add') }}</AppButton>
              </div>
              <TransitionGroup tag="div" class="mt-4 space-y-3" enter-active-class="transition duration-300" enter-from-class="opacity-0 -translate-y-2" leave-active-class="transition duration-200" leave-to-class="opacity-0">
                <div v-for="(c, i) in form.containers" :key="i" class="grid grid-cols-[1fr_auto] gap-3 rounded-xl bg-sunken p-3 sm:grid-cols-[2fr_1fr_1.4fr_auto] sm:items-end">
                  <FormField v-model="c.container_type" as="select" :label="$t('wizard.cargo.type')" class="col-span-2 sm:col-span-1">
                    <template #options><option v-for="ct in CONTAINERS" :key="ct" :value="ct">{{ ct }}</option></template>
                  </FormField>
                  <FormField v-model.number="c.quantity" type="number" min="1" inputmode="numeric" :label="$t('wizard.cargo.qty')" />
                  <FormField v-model.number="c.weight_kg" type="number" min="0" inputmode="decimal" :label="$t('wizard.cargo.weightPer')" :suffix="$t('units.kg')" />
                  <button type="button" class="mb-1 grid size-10 place-items-center self-end rounded-lg text-faint hover:bg-danger/10 hover:text-danger disabled:opacity-30" :disabled="form.containers.length === 1" :aria-label="$t('common.remove')" @click="form.containers.splice(i, 1)">
                    <AppIcon name="trash" :size="18" />
                  </button>
                </div>
              </TransitionGroup>
              <p v-if="errors.containers" class="mt-2 text-sm text-danger">{{ errors.containers }}</p>
            </div>

            <!-- Packages -->
            <div v-else class="card p-5">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <h3 class="font-bold">{{ $t('wizard.cargo.packages') }}</h3>
                <label class="flex items-center gap-2 text-sm font-semibold text-muted">
                  <input v-model="form.totals_only" type="checkbox" class="size-4 accent-brand" /> {{ $t('wizard.cargo.totalsOnly') }}
                </label>
              </div>
              <div v-if="form.totals_only" class="mt-4 grid gap-4 sm:grid-cols-2">
                <FormField v-model.number="form.total_weight_kg" type="number" min="0" inputmode="decimal" :label="$t('wizard.cargo.totalWeight')" :suffix="$t('units.kg')" />
                <FormField v-model.number="form.total_volume_cbm" type="number" min="0" step="0.01" inputmode="decimal" :label="$t('wizard.cargo.totalVolume')" :suffix="$t('units.cbm')" />
              </div>
              <template v-else>
                <TransitionGroup tag="div" class="mt-4 space-y-3" enter-active-class="transition duration-300" enter-from-class="opacity-0 -translate-y-2" leave-active-class="transition duration-200" leave-to-class="opacity-0">
                  <div v-for="(p, i) in form.packages" :key="i" class="grid grid-cols-3 gap-3 rounded-xl bg-sunken p-3 sm:grid-cols-[1.4fr_0.8fr_repeat(3,1fr)_1.2fr_auto] sm:items-end">
                    <FormField v-model="p.package_type" as="select" :label="$t('wizard.cargo.type')" class="col-span-2 sm:col-span-1">
                      <template #options><option v-for="pt in PACKAGES" :key="pt" :value="pt">{{ fmt.label('packages', pt) }}</option></template>
                    </FormField>
                    <FormField v-model.number="p.quantity" type="number" min="1" inputmode="numeric" :label="$t('wizard.cargo.qty')" />
                    <FormField v-model.number="p.length_cm" type="number" min="0" inputmode="decimal" :label="$t('wizard.cargo.l')" />
                    <FormField v-model.number="p.width_cm" type="number" min="0" inputmode="decimal" :label="$t('wizard.cargo.w')" />
                    <FormField v-model.number="p.height_cm" type="number" min="0" inputmode="decimal" :label="$t('wizard.cargo.h')" />
                    <FormField v-model.number="p.weight_kg" type="number" min="0" inputmode="decimal" :label="$t('wizard.cargo.weightPer')" class="col-span-2 sm:col-span-1" />
                    <button type="button" class="mb-1 grid size-10 place-items-center self-end rounded-lg text-faint hover:bg-danger/10 hover:text-danger disabled:opacity-30" :disabled="form.packages.length === 1" :aria-label="$t('common.remove')" @click="form.packages.splice(i, 1)">
                      <AppIcon name="trash" :size="18" />
                    </button>
                  </div>
                </TransitionGroup>
                <AppButton size="sm" variant="ghost" icon="plus" class="mt-3" @click="addPackage">{{ $t('wizard.cargo.addLine') }}</AppButton>
              </template>
              <p v-if="errors.weight" class="mt-2 text-sm text-danger">{{ errors.weight }}</p>
              <label class="mt-4 flex items-center gap-3 text-sm font-semibold"><input v-model="form.is_stackable" type="checkbox" class="size-5 accent-brand" /> {{ $t('wizard.cargo.stackable') }}</label>
            </div>

            <div class="grid gap-5 sm:grid-cols-[1fr_140px]">
              <FormField v-model.number="form.cargo_value" type="number" min="0" inputmode="decimal" :label="$t('wizard.cargo.value')" :hint="$t('wizard.cargo.valueHint')" />
              <FormField v-model="form.cargo_currency" as="select" :label="$t('fields.currency')">
                <template #options><option v-for="c in CURRENCIES" :key="c" :value="c">{{ c }}</option></template>
              </FormField>
            </div>
          </div>

          <!-- STEP 3: services -->
          <div v-else-if="step === 2" class="space-y-6">
            <div>
              <h2 class="text-2xl font-extrabold">{{ $t('wizard.services.title') }}</h2>
              <p class="mt-1 text-muted">{{ $t('wizard.services.subtitle') }}</p>
            </div>
            <div class="grid gap-3 sm:grid-cols-2">
              <label
                v-for="s in [
                  { k: 'need_customs_clearance', icon: 'file-text' },
                  { k: 'need_insurance', icon: 'shield-check' },
                  { k: 'need_warehousing', icon: 'boxes' },
                  { k: 'need_packing', icon: 'package' },
                ] as const"
                :key="s.k"
                class="flex cursor-pointer items-start gap-4 rounded-2xl border-2 p-4 transition-all"
                :class="form[s.k] ? 'border-brand bg-brand/6' : 'border-line bg-surface hover:border-brand/30'"
              >
                <input v-model="form[s.k]" type="checkbox" class="sr-only" />
                <span class="grid size-11 shrink-0 place-items-center rounded-xl transition-colors" :class="form[s.k] ? 'bg-brand-gradient text-white' : 'bg-sunken text-ink-soft'">
                  <AppIcon :name="s.icon" :size="20" />
                </span>
                <span class="flex-1">
                  <span class="block font-bold">{{ $t(`wizard.services.${s.k}.title`) }}</span>
                  <span class="mt-0.5 block text-sm text-muted">{{ $t(`wizard.services.${s.k}.text`) }}</span>
                </span>
                <AppIcon name="circle-check" :size="22" class="shrink-0 transition-all" :class="form[s.k] ? 'scale-100 text-brand' : 'scale-0'" />
              </label>
            </div>
            <div class="grid gap-5 sm:grid-cols-2">
              <FormField v-model="form.quote_currency" as="select" :label="$t('wizard.services.quoteCurrency')">
                <template #options><option v-for="c in CURRENCIES" :key="c" :value="c">{{ c }}</option></template>
              </FormField>
              <FormField v-model="form.valid_until" type="date" :min="inDays(1)" :label="$t('wizard.services.deadline')" :hint="$t('wizard.services.deadlineHint')" />
            </div>
            <FormField v-model="form.notes" as="textarea" :rows="4" :label="$t('wizard.services.notes')" :placeholder="$t('wizard.services.notesPh')" />
            <label class="flex cursor-pointer items-center gap-4 rounded-2xl border-2 border-dashed border-line-strong p-5 transition-colors hover:border-brand/50">
              <span class="grid size-11 place-items-center rounded-xl bg-sunken text-ink-soft"><AppIcon name="upload" :size="20" /></span>
              <span class="flex-1 text-sm">
                <span class="block font-bold">{{ file ? file.name : $t('wizard.services.attach') }}</span>
                <span class="text-muted">{{ $t('wizard.services.attachHint') }}</span>
              </span>
              <input type="file" class="sr-only" accept=".pdf,.jpg,.jpeg,.png,.xlsx,.xls,.doc,.docx" @change="onFile" />
            </label>
          </div>

          <!-- STEP 4: review + account -->
          <div v-else class="space-y-6">
            <div>
              <h2 class="text-2xl font-extrabold">{{ $t('wizard.review.title') }}</h2>
              <p class="mt-1 text-muted">{{ $t('wizard.review.subtitle') }}</p>
            </div>

            <div class="card divide-y divide-line">
              <div class="flex items-start justify-between gap-4 p-5">
                <div>
                  <p class="text-xs font-semibold text-faint uppercase">{{ $t('wizard.steps.route') }}</p>
                  <p class="mt-1 font-bold">
                    {{ form.origin_city }}, {{ form.origin_country }} <AppIcon name="arrow-right" :size="14" flip class="mx-1 inline" /> {{ form.destination_city }}, {{ form.destination_country }}
                  </p>
                  <p class="mt-1 text-sm text-muted">{{ mode && $t(`modes.${mode.code}.name`) }} · {{ $t('wizard.review.ready') }} {{ fmt.date(form.ready_date) }}<template v-if="form.incoterm"> · {{ form.incoterm }}</template></p>
                </div>
                <button type="button" class="text-sm font-semibold text-brand" @click="goto(0)">{{ $t('common.edit') }}</button>
              </div>
              <div class="flex items-start justify-between gap-4 p-5">
                <div>
                  <p class="text-xs font-semibold text-faint uppercase">{{ $t('wizard.steps.cargo') }}</p>
                  <p class="mt-1 font-bold">{{ form.commodity }}</p>
                  <p class="mt-1 text-sm text-muted">
                    <template v-if="usesContainers">{{ form.containers.map((c) => `${c.quantity} × ${c.container_type}`).join(', ') }}</template>
                    <template v-else>{{ fmt.weight(totals.weight) }}<template v-if="totals.volume"> · {{ fmt.number(totals.volume, 2) }} {{ $t('units.cbm') }}</template></template>
                    · {{ fmt.label('categories', form.cargo_category) }}
                  </p>
                </div>
                <button type="button" class="text-sm font-semibold text-brand" @click="goto(1)">{{ $t('common.edit') }}</button>
              </div>
            </div>

            <ClientOnly>
              <div v-if="!isLoggedIn" class="card p-5 sm:p-6">
                <div class="mb-5 inline-grid grid-cols-2 rounded-xl bg-sunken p-1 text-sm font-semibold">
                  <button type="button" class="rounded-lg px-4 py-2 transition-all" :class="account.mode === 'register' ? 'bg-surface shadow-sm' : 'text-muted'" @click="account.mode = 'register'">{{ $t('wizard.review.newAccount') }}</button>
                  <button type="button" class="rounded-lg px-4 py-2 transition-all" :class="account.mode === 'login' ? 'bg-surface shadow-sm' : 'text-muted'" @click="account.mode = 'login'">{{ $t('wizard.review.haveAccount') }}</button>
                </div>
                <p class="mb-5 text-sm text-muted">{{ account.mode === 'register' ? $t('wizard.review.accountWhy') : $t('wizard.review.loginWhy') }}</p>
                <div class="grid gap-4 sm:grid-cols-2">
                  <FormField v-if="account.mode === 'register'" v-model="account.full_name" :label="$t('fields.fullName')" required autocomplete="name" :error="errors.full_name" />
                  <FormField v-if="account.mode === 'register'" v-model="account.company_name" :label="$t('fields.company')" autocomplete="organization" />
                  <FormField v-model="account.email" type="email" :label="$t('fields.email')" required autocomplete="email" dir="ltr" :error="errors.email" />
                  <FormField v-if="account.mode === 'register'" v-model="account.phone" type="tel" :label="$t('fields.phone')" autocomplete="tel" dir="ltr" />
                  <FormField v-model="account.password" type="password" :label="$t('fields.password')" required :autocomplete="account.mode === 'register' ? 'new-password' : 'current-password'" :error="errors.password" :class="account.mode === 'login' && 'sm:col-span-2'" />
                </div>
              </div>
              <div v-else class="flex items-center gap-3 rounded-2xl bg-success/10 p-4 text-sm">
                <AppIcon name="circle-check" class="text-success" />
                {{ $t('wizard.review.signedInAs', { name: me?.full_name }) }}
              </div>
            </ClientOnly>

            <p class="flex items-start gap-2 text-xs text-faint">
              <AppIcon name="lock" :size="14" class="mt-0.5 shrink-0" /> {{ $t('wizard.review.privacy') }}
            </p>
          </div>
        </Motion>
      </AnimatePresence>

      <!-- Nav -->
      <div class="glass sticky bottom-0 z-10 -mx-4 mt-8 flex items-center gap-3 border-x-0 border-b-0 px-4 py-3 safe-bottom sm:static sm:mx-0 sm:border-0 sm:bg-transparent sm:p-0 sm:backdrop-blur-none">
        <AppButton v-if="step > 0" variant="secondary" size="lg" icon="arrow-left" @click="back">{{ $t('common.back') }}</AppButton>
        <AppButton v-if="step < STEPS.length - 1" variant="primary" size="lg" icon-end="arrow-right" class="ms-auto flex-1 sm:flex-none" @click="next">{{ $t('common.continue') }}</AppButton>
        <AppButton v-else variant="accent" size="lg" icon-end="send" :loading="submitting" class="ms-auto flex-1 sm:flex-none" @click="submit">{{ $t('wizard.submit') }}</AppButton>
      </div>
    </div>

    <!-- Live summary -->
    <aside class="hidden lg:block">
      <div class="sticky top-28 space-y-4">
        <div class="overflow-hidden rounded-3xl bg-night-950 p-6 text-white">
          <p class="text-xs font-semibold tracking-wide text-white/50 uppercase">{{ $t('wizard.summary') }}</p>
          <div class="mt-4 flex items-center gap-3">
            <span class="grid size-11 place-items-center rounded-xl bg-brand-gradient"><AppIcon :name="mode?.icon || 'package'" :size="20" /></span>
            <span class="font-bold">{{ mode ? $t(`modes.${mode.code}.name`) : '—' }}</span>
          </div>
          <div class="mt-5 space-y-2 text-sm">
            <p class="flex items-center gap-2"><span class="size-2 rounded-full bg-brand" />{{ form.origin_city || '…' }}<span v-if="form.origin_country" class="text-white/50">· {{ form.origin_country }}</span></p>
            <p class="ms-[3px] h-4 border-s border-dashed border-white/30" />
            <p class="flex items-center gap-2"><span class="size-2 rounded-full bg-lagoon" />{{ form.destination_city || '…' }}<span v-if="form.destination_country" class="text-white/50">· {{ form.destination_country }}</span></p>
          </div>
          <dl class="mt-6 grid grid-cols-2 gap-3 border-t border-white/10 pt-5 text-sm">
            <div><dt class="text-white/50">{{ $t('wizard.grossWeight') }}</dt><dd class="font-bold tabular-nums">{{ fmt.weight(totals.weight) }}</dd></div>
            <div v-if="!usesContainers"><dt class="text-white/50">{{ $t('wizard.volume') }}</dt><dd class="font-bold tabular-nums">{{ fmt.number(totals.volume, 2) }} {{ $t('units.cbm') }}</dd></div>
            <div v-if="!usesContainers" class="col-span-2"><dt class="text-white/50">{{ $t('wizard.chargeable') }}</dt><dd class="text-lg font-extrabold text-lagoon tabular-nums">{{ fmt.weight(chargeable) }}</dd></div>
            <div v-else><dt class="text-white/50">{{ $t('wizard.units') }}</dt><dd class="font-bold tabular-nums">{{ fmt.number(totals.count) }}</dd></div>
          </dl>
        </div>
        <ul class="card space-y-3 p-5 text-sm">
          <li v-for="k in ['why1', 'why2', 'why3']" :key="k" class="flex items-start gap-2.5"><AppIcon name="circle-check" :size="18" class="mt-0.5 shrink-0 text-success" />{{ $t(`wizard.${k}`) }}</li>
        </ul>
      </div>
    </aside>
  </div>
</template>
