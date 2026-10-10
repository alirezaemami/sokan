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

const { data: c, status: loading, error } = await useAsyncData(`admin-cust-${id.value}`, () => api.admin.customer(id.value), { server: false })
useHead({ title: computed(() => c.value?.full_name || t('admin.nav.customers')) })

const confirmOpen = ref(false)
const busy = ref(false)
async function toggleBlock() {
  busy.value = true
  try {
    c.value = await api.admin.setCustomerBlocked(id.value, !c.value?.is_blocked)
    confirmOpen.value = false
    toast.success(c.value?.is_blocked ? t('admin.customers.blockedDone') : t('admin.customers.unblockedDone'))
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    busy.value = false
  }
}

const verifying = ref(false)
async function markVerified() {
  if (!c.value?.user) return
  verifying.value = true
  try {
    await api.admin.markEmailVerified(c.value.user)
    c.value = await api.admin.customer(id.value)
    toast.success(t('admin.emailUnverified.done'))
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    verifying.value = false
  }
}

const facts = computed(() => {
  const v = c.value
  if (!v) return []
  return [
    { label: t('fields.email'), value: v.email, href: v.email ? `mailto:${v.email}` : undefined },
    { label: t('fields.phone'), value: v.phone },
    { label: t('fields.company'), value: v.company_name },
    { label: t('admin.customers.type'), value: v.customer_type },
    { label: t('fields.country'), value: [v.city, countryLabel(v.country)].filter(Boolean).join(', ') },
    { label: t('admin.forwarders.joined'), value: fmt.date(v.creation) },
    { label: t('admin.customers.lastLogin'), value: v.last_login ? fmt.relative(v.last_login) : t('admin.neverLoggedIn') },
    { label: t('admin.customers.bookings'), value: `${v.bookings_count} / ${v.requests_count}` },
  ]
})
</script>

<template>
  <div>
    <PortalHeading :title="c?.full_name || ''" back="/admin/customers">
      <AppButton v-if="c" :variant="c.is_blocked ? 'accent' : 'danger'" :icon="c.is_blocked ? 'lock-open' : 'ban'" @click="confirmOpen = true">
        {{ c.is_blocked ? $t('admin.customers.unblock') : $t('admin.customers.block') }}
      </AppButton>
    </PortalHeading>

    <div v-if="loading === 'pending' && !c" class="skeleton h-80" />
    <div v-else-if="error" class="card"><EmptyState icon="alert" :title="$t('admin.notFound')" /></div>
    <template v-else-if="c">
      <p v-if="c.is_blocked" class="mb-6 rounded-2xl bg-danger/10 p-4 text-sm text-danger">{{ $t('admin.customers.blockedNote') }}</p>
      <div v-if="c.email_verified === false" class="mb-6 flex flex-wrap items-center gap-3 rounded-2xl bg-warning/12 p-4 text-sm">
        <AppIcon name="mail" class="shrink-0 text-warning" />
        <p class="min-w-0 flex-1">{{ $t('admin.emailUnverified.customer') }}</p>
        <AppButton size="sm" variant="secondary" icon="check" :loading="verifying" @click="markVerified">{{ $t('admin.emailUnverified.mark') }}</AppButton>
      </div>
      <div class="grid gap-4 lg:grid-cols-3">
        <section class="card p-5 lg:col-span-1">
          <h2 class="mb-4 font-semibold">{{ $t('admin.customers.profile') }}</h2>
          <Facts :items="facts" class="!grid-cols-1" />
        </section>
        <section class="card overflow-hidden p-0 lg:col-span-2">
          <div class="flex items-center justify-between border-b border-line px-5 py-4">
            <h2 class="font-semibold">{{ $t('admin.nav.requests') }}</h2>
            <NuxtLinkLocale :to="`/admin/requests?customer=${c.name}`" class="text-sm font-semibold text-sea hover:underline">{{ $t('common.viewAll') }}</NuxtLinkLocale>
          </div>
          <ul v-if="c.requests.length" class="divide-y divide-line">
            <li v-for="r in c.requests" :key="r.name">
              <NuxtLinkLocale :to="`/admin/requests/${r.name}`" class="flex items-center gap-3 px-5 py-3 hover:bg-sunken/60">
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-semibold">{{ r.title }}</p>
                  <p class="text-xs text-faint"><span class="font-mono">{{ r.name }}</span> · {{ fmt.relative(r.creation) }}</p>
                </div>
                <span class="hidden text-xs text-muted sm:block">{{ $t('admin.requests.quotesN', { n: r.quote_count }) }}</span>
                <StatusPill :status="r.status" />
              </NuxtLinkLocale>
            </li>
          </ul>
          <EmptyState v-else icon="inbox" :title="$t('admin.requests.empty')" />
        </section>
      </div>
    </template>

    <ConfirmDialog
      v-model="confirmOpen"
      :title="c?.is_blocked ? $t('admin.customers.unblock') : $t('admin.customers.block')"
      :text="c?.is_blocked ? $t('admin.customers.unblockText') : $t('admin.customers.blockText')"
      :confirm-label="c?.is_blocked ? $t('admin.customers.unblock') : $t('admin.customers.block')"
      :variant="c?.is_blocked ? 'accent' : 'danger'"
      :loading="busy"
      @confirm="toggleBlock"
    />
  </div>
</template>
