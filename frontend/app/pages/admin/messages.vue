<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'admin' })
const { t } = useI18n()
useHead({ title: t('admin.nav.messages') })
const api = useSokan()
const fmt = useFormat()
const toast = useToast()
const errorMessage = useErrorMessage()
const { refresh: refreshCounts } = useAdminAttention()

const status = ref('New')
const page = ref(1)
watch(status, () => (page.value = 1))
const { data, status: loading, refresh } = await useAsyncData('admin-messages', () => api.admin.messages({ status: status.value, page: page.value }), {
  server: false,
  watch: [status, page],
})
const tabs = computed(() => {
  const c = data.value?.counts || {}
  return [
    ...['New', 'Replied', 'Closed'].map((s) => ({ value: s, label: t(`admin.messages.status.${s}`), count: c[s] || 0 })),
    { value: '', label: t('common.all') },
  ]
})

const busy = ref('')
async function setStatus(name: string, s: string) {
  busy.value = name + s
  try {
    await api.admin.setMessageStatus(name, s)
    toast.success(t('common.saved'))
    await Promise.all([refresh(), refreshCounts()])
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    busy.value = ''
  }
}

const copied = ref('')
async function copy(email: string) {
  try {
    await navigator.clipboard.writeText(email)
    copied.value = email
    setTimeout(() => (copied.value = ''), 1500)
  } catch {
    // Clipboard can be refused; the address is still visible to select.
  }
}
</script>

<template>
  <div>
    <PortalHeading :title="$t('admin.nav.messages')" :subtitle="$t('admin.messages.subtitle')" />
    <FilterTabs v-model="status" :options="tabs" />

    <div v-if="loading === 'pending' && !data" class="space-y-3"><div v-for="i in 3" :key="i" class="skeleton h-36" /></div>
    <div v-else-if="data?.items.length" class="space-y-3">
      <article v-for="m in data.items" :key="m.name" class="card p-4 sm:p-5">
        <div class="flex flex-wrap items-start gap-3">
          <div class="min-w-0 flex-1">
            <p class="font-semibold">{{ m.subject || $t('admin.messages.noSubject') }}</p>
            <p class="mt-0.5 text-sm text-muted">
              {{ m.full_name }}<template v-if="m.company"> · {{ m.company }}</template>
              <span v-if="m.audience" class="ms-1 rounded-full bg-sunken px-2 py-0.5 text-xs">{{ m.audience }}</span>
            </p>
            <p class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-faint">
              <span class="select-all font-mono">{{ m.email }}</span>
              <button type="button" class="font-semibold text-sea hover:underline" @click="copy(m.email)">{{ copied === m.email ? $t('admin.copied') : $t('admin.copy') }}</button>
              <span v-if="m.phone" class="select-all">{{ m.phone }}</span>
              <span>{{ fmt.relative(m.creation) }}</span>
            </p>
          </div>
          <span class="rounded-full bg-sunken px-2.5 py-1 text-xs font-semibold" :class="m.status === 'New' && '!bg-buoy/12 text-buoy'">{{ $t(`admin.messages.status.${m.status}`) }}</span>
        </div>
        <p class="mt-3 rounded-xl bg-sunken p-4 text-sm leading-relaxed whitespace-pre-line text-ink-soft">{{ m.message }}</p>
        <div class="mt-4 flex flex-wrap justify-end gap-2">
          <AppButton :href="`mailto:${m.email}?subject=${encodeURIComponent('Re: ' + (m.subject || ''))}`" size="sm" variant="ghost" icon="mail">{{ $t('admin.messages.reply') }}</AppButton>
          <AppButton v-if="m.status !== 'Replied'" size="sm" variant="secondary" :loading="busy === m.name + 'Replied'" @click="setStatus(m.name, 'Replied')">{{ $t('admin.messages.markReplied') }}</AppButton>
          <AppButton v-if="m.status !== 'Closed'" size="sm" variant="primary" :loading="busy === m.name + 'Closed'" @click="setStatus(m.name, 'Closed')">{{ $t('admin.messages.close') }}</AppButton>
        </div>
      </article>
    </div>
    <div v-else class="card"><EmptyState icon="mail" :title="$t('admin.messages.empty')" /></div>
    <AppPagination v-if="data" v-model="page" class="mt-6" :total="data.total" :page-size="20" />
  </div>
</template>
