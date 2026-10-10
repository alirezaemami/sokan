<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'admin' })
const { t } = useI18n()
useHead({ title: t('admin.nav.reviews') })
const api = useSokan()
const fmt = useFormat()
const toast = useToast()
const errorMessage = useErrorMessage()
const { refresh: refreshCounts } = useAdminAttention()

const status = ref('Pending')
const page = ref(1)
watch(status, () => (page.value = 1))
const { data, status: loading, refresh } = await useAsyncData('admin-reviews', () => api.admin.reviews({ status: status.value, page: page.value }), {
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

const busy = ref('')
async function moderate(name: string, action: 'approve' | 'reject') {
  busy.value = name + action
  try {
    await api.admin.moderateReview(name, action)
    toast.success(action === 'approve' ? t('admin.reviews.approved') : t('admin.reviews.rejected'))
    await Promise.all([refresh(), refreshCounts()])
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    busy.value = ''
  }
}
</script>

<template>
  <div>
    <PortalHeading :title="$t('admin.nav.reviews')" :subtitle="$t('admin.reviews.subtitle')" />
    <FilterTabs v-model="status" :options="tabs" />

    <div v-if="loading === 'pending' && !data" class="space-y-3"><div v-for="i in 3" :key="i" class="skeleton h-32" /></div>
    <div v-else-if="data?.items.length" class="space-y-3">
      <article v-for="rv in data.items" :key="rv.name" class="card p-4 sm:p-5">
        <div class="flex flex-wrap items-start gap-3">
          <div class="min-w-0 flex-1">
            <p class="text-lg leading-none text-warning" :aria-label="$t('admin.reviews.stars', { n: rv.rating })">
              {{ '★'.repeat(rv.rating) }}<span class="text-line-strong">{{ '★'.repeat(5 - rv.rating) }}</span>
            </p>
            <p class="mt-2 text-sm">
              <b>{{ rv.customer_name }}</b>
              <span class="text-muted"> {{ $t('admin.reviews.about') }} </span>
              <NuxtLinkLocale :to="`/admin/forwarders/${rv.forwarder}`" class="font-semibold text-sea hover:underline">{{ rv.company_name }}</NuxtLinkLocale>
            </p>
            <p class="mt-0.5 text-xs text-faint">
              <NuxtLinkLocale :to="`/admin/requests/${rv.request}`" class="font-mono hover:text-sea">{{ rv.request }}</NuxtLinkLocale> · {{ fmt.relative(rv.creation) }}
            </p>
          </div>
          <StatusPill :status="rv.status" />
        </div>
        <blockquote v-if="rv.comment" class="mt-3 rounded-xl bg-sunken p-4 text-sm leading-relaxed whitespace-pre-line text-ink-soft">{{ rv.comment }}</blockquote>
        <p v-else class="mt-3 text-sm text-faint italic">{{ $t('admin.reviews.noComment') }}</p>
        <div class="mt-4 flex flex-wrap items-center gap-2">
          <p v-if="rv.moderated_by" class="me-auto text-xs text-faint">{{ $t('admin.reviewedBy', { who: rv.moderated_by, when: fmt.date(rv.moderated_on, 'short') }) }}</p>
          <span v-else class="me-auto" />
          <AppButton v-if="rv.status !== 'Rejected'" size="sm" variant="ghost" :loading="busy === rv.name + 'reject'" @click="moderate(rv.name, 'reject')">{{ $t('admin.reviews.hide') }}</AppButton>
          <AppButton v-if="rv.status !== 'Approved'" size="sm" variant="accent" icon="check" :loading="busy === rv.name + 'approve'" @click="moderate(rv.name, 'approve')">{{ $t('admin.reviews.publish') }}</AppButton>
        </div>
      </article>
    </div>
    <div v-else class="card"><EmptyState icon="star" :title="$t('admin.reviews.empty')" /></div>
    <AppPagination v-if="data" v-model="page" class="mt-6" :total="data.total" :page-size="20" />
  </div>
</template>
