<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'admin' })
const { t } = useI18n()
useHead({ title: t('admin.nav.settings') })
const api = useSokan()
const fmt = useFormat()
const toast = useToast()
const errorMessage = useErrorMessage()
const { me } = useAuth()
const route = useRoute()

const TABS = ['platform', 'plans', 'modes', 'managers'] as const
const tab = ref<(typeof TABS)[number]>((TABS as readonly string[]).includes(String(route.query.tab)) ? (route.query.tab as any) : 'platform')
const tabOptions = computed(() => TABS.map((k) => ({ value: k, label: t(`admin.settings.tabs.${k}`) })))

async function attempt<T>(call: () => Promise<T>, done = t('common.saved')) {
  try {
    const res = await call()
    toast.success(done)
    return res
  } catch (e) {
    toast.error(errorMessage(e))
    return null
  }
}

// ---- platform
const { data: settings } = await useAsyncData('admin-settings', () => api.admin.settings(), { server: false })
const form = reactive<Record<string, any>>({})
watch(settings, (s) => s && Object.assign(form, s), { immediate: true })
const savingSettings = ref(false)
async function saveSettings() {
  savingSettings.value = true
  const res = await attempt(() => api.admin.updateSettings({ ...form }))
  if (res) settings.value = res
  savingSettings.value = false
}
const SWITCHES = ['auto_approve_forwarders', 'auto_publish_requests', 'match_transport_mode', 'match_coverage', 'refund_unlock_if_cancelled'] as const

// ---- plans
const { data: plans, refresh: refreshPlans } = await useAsyncData('admin-plans', () => api.admin.plans(), { server: false })
const planOpen = ref(false)
const plan = reactive<Record<string, any>>({})
const featuresText = ref('')
function editPlan(p?: Record<string, any>) {
  Object.keys(plan).forEach((k) => delete plan[k])
  Object.assign(plan, p || { plan_name: '', is_active: 1, currency: settings.value?.default_currency || 'USD', monthly_fee: 0, view_fee: 0, quote_fee: 0, free_views_per_month: 0, free_quotes_per_month: 0, sort_order: (plans.value?.length || 0) + 1 })
  featuresText.value = (p?.features || []).join('\n')
  planOpen.value = true
}
const savingPlan = ref(false)
async function savePlan() {
  savingPlan.value = true
  const res = await attempt(() => api.admin.savePlan({ ...plan, features: featuresText.value.split('\n') }))
  if (res) {
    plans.value = res
    planOpen.value = false
  }
  savingPlan.value = false
}

// ---- modes
const { data: modes } = await useAsyncData('admin-modes', () => api.admin.modes(), { server: false })
const modeBusy = ref('')
async function toggleMode(m: Record<string, any>) {
  modeBusy.value = m.name
  const res = await attempt(() => api.admin.saveMode(m.name, { is_active: m.is_active ? 0 : 1 }))
  if (res) modes.value = res
  modeBusy.value = ''
}

// ---- managers
const { data: managers } = await useAsyncData('admin-managers', () => api.admin.managers(), { server: false })
const invite = reactive({ email: '', full_name: '' })
const inviting = ref(false)
async function addManager() {
  inviting.value = true
  const res = await attempt(() => api.admin.addManager(invite.email, invite.full_name || undefined), t('admin.settings.managerAdded'))
  if (res) {
    managers.value = res
    Object.assign(invite, { email: '', full_name: '' })
  }
  inviting.value = false
}
const removing = ref<Record<string, any> | null>(null)
const removeOpen = ref(false)
const removeBusy = ref(false)
async function removeManager() {
  if (!removing.value) return
  removeBusy.value = true
  const res = await attempt(() => api.admin.removeManager(removing.value!.name), t('admin.settings.managerRemoved'))
  if (res) {
    managers.value = res
    removeOpen.value = false
  }
  removeBusy.value = false
}
</script>

<template>
  <div>
    <PortalHeading :title="$t('admin.nav.settings')" :subtitle="$t('admin.settings.subtitle')" />
    <FilterTabs v-model="tab" :options="tabOptions" />

    <!-- Platform -->
    <form v-if="tab === 'platform'" class="space-y-4" @submit.prevent="saveSettings">
      <div v-if="!settings" class="skeleton h-96" />
      <template v-else>
        <section class="card grid gap-4 p-5 sm:grid-cols-2">
          <h2 class="font-semibold sm:col-span-2">{{ $t('admin.settings.general') }}</h2>
          <FormField v-model="form.platform_name" :label="$t('admin.settings.f.platform_name')" />
          <FormField v-model="form.default_currency" :label="$t('admin.settings.f.default_currency')" :hint="$t('admin.settings.h.default_currency')" />
          <FormField v-model="form.support_email" type="email" :label="$t('admin.settings.f.support_email')" />
          <FormField v-model="form.support_phone" type="tel" :label="$t('admin.settings.f.support_phone')" />
          <FormField v-model="form.frontend_url" class="sm:col-span-2" :label="$t('admin.settings.f.frontend_url')" :hint="$t('admin.settings.h.frontend_url')" placeholder="https://www.sokan.net" />
        </section>

        <section class="card grid gap-4 p-5 sm:grid-cols-2">
          <h2 class="font-semibold sm:col-span-2">{{ $t('admin.settings.billing') }}</h2>
          <FormField v-model.number="form.default_view_fee" type="number" min="0" step="0.01" :label="$t('admin.settings.f.default_view_fee')" :hint="$t('admin.settings.h.planFirst')" :suffix="form.default_currency" />
          <FormField v-model.number="form.default_quote_fee" type="number" min="0" step="0.01" :label="$t('admin.settings.f.default_quote_fee')" :hint="$t('admin.settings.h.planFirst')" :suffix="form.default_currency" />
          <FormField v-model.number="form.signup_bonus" type="number" min="0" step="0.01" :label="$t('admin.settings.f.signup_bonus')" :hint="$t('admin.settings.h.signup_bonus')" :suffix="form.default_currency" />
          <FormField v-model.number="form.low_balance_threshold" type="number" min="0" step="0.01" :label="$t('admin.settings.f.low_balance_threshold')" :suffix="form.default_currency" />
          <FormField v-model="form.topup_instructions" as="textarea" class="sm:col-span-2" :label="$t('admin.settings.f.topup_instructions')" :hint="$t('admin.settings.h.topup_instructions')" />
        </section>

        <section class="card grid gap-4 p-5 sm:grid-cols-2">
          <h2 class="font-semibold sm:col-span-2">{{ $t('admin.settings.marketplace') }}</h2>
          <FormField v-model.number="form.request_validity_days" type="number" min="1" max="365" :label="$t('admin.settings.f.request_validity_days')" />
          <FormField v-model.number="form.max_quotes_per_request" type="number" min="0" :label="$t('admin.settings.f.max_quotes_per_request')" :hint="$t('admin.settings.h.max_quotes_per_request')" />
          <label v-for="s in SWITCHES" :key="s" class="flex cursor-pointer items-start gap-3 rounded-xl bg-sunken p-4 sm:col-span-2">
            <input v-model="form[s]" type="checkbox" :true-value="1" :false-value="0" class="mt-0.5 size-4 shrink-0 accent-[var(--sea)]" />
            <span class="min-w-0">
              <span class="block text-sm font-semibold">{{ $t(`admin.settings.f.${s}`) }}</span>
              <span class="block text-xs text-muted">{{ $t(`admin.settings.h.${s}`) }}</span>
            </span>
          </label>
        </section>
        <div class="sticky bottom-20 flex justify-end lg:bottom-4">
          <AppButton type="submit" variant="accent" icon="check" :loading="savingSettings">{{ $t('common.saveChanges') }}</AppButton>
        </div>
      </template>
    </form>

    <!-- Plans -->
    <div v-else-if="tab === 'plans'">
      <div class="mb-4 flex justify-end"><AppButton icon="plus" @click="editPlan()">{{ $t('admin.settings.newPlan') }}</AppButton></div>
      <div v-if="!plans" class="skeleton h-64" />
      <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <article v-for="p in plans" :key="p.name" class="card flex flex-col p-5" :class="!p.is_active && 'opacity-60'">
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <h3 class="font-display text-2xl">{{ p.plan_name }}</h3>
              <p class="text-xs text-faint">{{ $t('admin.settings.subscribers', { n: p.subscribers }) }}</p>
            </div>
            <div class="flex flex-wrap justify-end gap-1">
              <span v-if="p.is_default" class="rounded-full bg-sea/10 px-2 py-0.5 text-xs font-semibold text-sea">{{ $t('admin.settings.default') }}</span>
              <span v-if="!p.is_active" class="rounded-full bg-sunken px-2 py-0.5 text-xs font-semibold text-muted">{{ $t('admin.settings.inactive') }}</span>
            </div>
          </div>
          <dl class="mt-4 space-y-1.5 text-sm">
            <div class="flex justify-between"><dt class="text-muted">{{ $t('admin.settings.p.monthly_fee') }}</dt><dd class="tabular-nums">{{ fmt.money(p.monthly_fee, p.currency) }}</dd></div>
            <div class="flex justify-between"><dt class="text-muted">{{ $t('admin.settings.p.view_fee') }}</dt><dd class="tabular-nums">{{ fmt.money(p.view_fee, p.currency) }}</dd></div>
            <div class="flex justify-between"><dt class="text-muted">{{ $t('admin.settings.p.quote_fee') }}</dt><dd class="tabular-nums">{{ fmt.money(p.quote_fee, p.currency) }}</dd></div>
            <div class="flex justify-between"><dt class="text-muted">{{ $t('admin.settings.p.free') }}</dt><dd class="tabular-nums">{{ p.free_views_per_month }} / {{ p.free_quotes_per_month }}</dd></div>
          </dl>
          <AppButton variant="secondary" size="sm" class="mt-5 self-start" icon="sliders" @click="editPlan(p)">{{ $t('common.edit') }}</AppButton>
        </article>
      </div>
    </div>

    <!-- Transport modes -->
    <div v-else-if="tab === 'modes'">
      <p class="mb-4 text-sm text-muted">{{ $t('admin.settings.modesHint') }}</p>
      <div v-if="!modes" class="skeleton h-64" />
      <ul v-else class="card divide-y divide-line p-0">
        <li v-for="m in modes" :key="m.name" class="flex items-center gap-4 px-5 py-3.5">
          <span class="grid size-10 shrink-0 place-items-center rounded-xl bg-sunken text-ink-soft"><AppIcon :name="m.icon" :size="19" /></span>
          <div class="min-w-0 flex-1">
            <p class="truncate font-semibold">{{ $t(`modes.${m.code}.name`) }}</p>
            <p class="truncate text-xs text-faint">{{ m.category }} · {{ $t('admin.settings.requestsN', { n: m.requests }) }}</p>
          </div>
          <button
            type="button"
            role="switch"
            :aria-checked="!!m.is_active"
            :aria-label="$t(`modes.${m.code}.name`)"
            :disabled="modeBusy === m.name"
            class="relative h-6 w-11 shrink-0 rounded-full transition-colors"
            :class="m.is_active ? 'bg-sea' : 'bg-line-strong'"
            @click="toggleMode(m)"
          >
            <span class="absolute top-0.5 size-5 rounded-full bg-white shadow transition-[inset-inline-start]" :class="m.is_active ? 'start-5.5' : 'start-0.5'" />
          </button>
        </li>
      </ul>
    </div>

    <!-- Managers -->
    <div v-else class="grid gap-4 lg:grid-cols-5">
      <section class="card overflow-hidden p-0 lg:col-span-3">
        <h2 class="border-b border-line px-5 py-4 font-semibold">{{ $t('admin.settings.managers') }}</h2>
        <ul v-if="managers?.length" class="divide-y divide-line">
          <li v-for="u in managers" :key="u.name" class="flex items-center gap-3 px-5 py-3">
            <span class="grid size-9 place-items-center rounded-full bg-sea/10 text-sm font-bold text-sea">{{ (u.full_name || u.name).charAt(0) }}</span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold">{{ u.full_name }} <span v-if="u.name === me?.user" class="font-normal text-faint">({{ $t('admin.settings.you') }})</span></p>
              <p class="truncate text-xs text-faint">{{ u.name }} · {{ u.last_login ? $t('admin.lastLogin', { when: fmt.relative(u.last_login) }) : $t('admin.neverLoggedIn') }}</p>
            </div>
            <AppButton v-if="u.name !== me?.user" variant="ghost" size="sm" @click="(removing = u), (removeOpen = true)">{{ $t('common.remove') }}</AppButton>
          </li>
        </ul>
        <EmptyState v-else icon="users" :title="$t('admin.settings.noManagers')" />
      </section>
      <form class="card space-y-4 p-5 lg:col-span-2" @submit.prevent="addManager">
        <h2 class="font-semibold">{{ $t('admin.settings.addManager') }}</h2>
        <p class="text-sm text-muted">{{ $t('admin.settings.addManagerHint') }}</p>
        <FormField v-model="invite.email" type="email" :label="$t('fields.email')" required />
        <FormField v-model="invite.full_name" :label="$t('fields.fullName')" />
        <AppButton type="submit" variant="accent" icon="plus" :loading="inviting" :disabled="!invite.email">{{ $t('admin.settings.addManager') }}</AppButton>
      </form>
    </div>

    <AppModal v-model="planOpen" :title="plan.name ? $t('admin.settings.editPlan', { name: plan.plan_name }) : $t('admin.settings.newPlan')" size="lg">
      <div class="grid gap-4 sm:grid-cols-2">
        <FormField v-if="!plan.name" v-model="plan.plan_name" class="sm:col-span-2" :label="$t('admin.settings.p.plan_name')" required />
        <FormField v-model.number="plan.monthly_fee" type="number" min="0" step="0.01" :label="$t('admin.settings.p.monthly_fee')" :suffix="plan.currency" />
        <FormField v-model="plan.badge" :label="$t('admin.settings.p.badge')" :placeholder="$t('admin.settings.p.badgeHint')" />
        <FormField v-model.number="plan.view_fee" type="number" min="0" step="0.01" :label="$t('admin.settings.p.view_fee')" :suffix="plan.currency" />
        <FormField v-model.number="plan.quote_fee" type="number" min="0" step="0.01" :label="$t('admin.settings.p.quote_fee')" :suffix="plan.currency" />
        <FormField v-model.number="plan.free_views_per_month" type="number" min="0" :label="$t('admin.settings.p.free_views_per_month')" />
        <FormField v-model.number="plan.free_quotes_per_month" type="number" min="0" :label="$t('admin.settings.p.free_quotes_per_month')" />
        <FormField v-model.number="plan.sort_order" type="number" :label="$t('admin.settings.p.sort_order')" />
        <FormField v-model="plan.currency" :label="$t('fields.currency')" />
        <FormField v-model="plan.description" as="textarea" class="sm:col-span-2" :label="$t('admin.settings.p.description')" />
        <FormField v-model="featuresText" as="textarea" class="sm:col-span-2" :label="$t('admin.settings.p.features')" :hint="$t('admin.settings.p.featuresHint')" />
        <div class="flex flex-wrap gap-x-6 gap-y-3 sm:col-span-2">
          <label v-for="flag in ['is_active', 'is_default', 'priority_listing']" :key="flag" class="flex cursor-pointer items-center gap-2 text-sm">
            <input v-model="plan[flag]" type="checkbox" :true-value="1" :false-value="0" class="size-4 accent-[var(--sea)]" />
            {{ $t(`admin.settings.p.${flag}`) }}
          </label>
        </div>
      </div>
      <template #footer>
        <AppButton variant="ghost" @click="planOpen = false">{{ $t('common.cancel') }}</AppButton>
        <AppButton :loading="savingPlan" :disabled="!plan.name && !plan.plan_name?.trim()" @click="savePlan">{{ $t('common.saveChanges') }}</AppButton>
      </template>
    </AppModal>

    <ConfirmDialog
      v-model="removeOpen"
      :title="$t('admin.settings.removeManager')"
      :text="removing ? $t('admin.settings.removeText', { name: removing.full_name || removing.name }) : ''"
      :confirm-label="$t('common.remove')"
      variant="danger"
      :loading="removeBusy"
      @confirm="removeManager"
    />
  </div>
</template>
