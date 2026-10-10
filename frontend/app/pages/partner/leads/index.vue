<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'forwarder' })
const { t } = useI18n()
useHead({ title: t('portal.nav.leads') })
const api = useSokan()
const { modes, load } = useModes()
onMounted(load)

const status = ref('')
const mode = ref('')
const onlyOpen = ref(true)
const page = ref(1)

const { data, status: loading } = await useAsyncData(
  'partner-leads',
  () => api.partner.leads({ status: status.value || undefined, mode: mode.value || undefined, only_open: onlyOpen.value ? 1 : 0, page: page.value }),
  { server: false, watch: [status, mode, onlyOpen, page] },
)
watch([status, mode, onlyOpen], () => (page.value = 1))

const tabs = computed(() => [
  { value: '', label: t('common.all') },
  ...['New', 'Unlocked', 'Quoted', 'Declined'].map((s) => ({ value: s, label: t(`leadStatus.${s}`) })),
])
</script>

<template>
  <div>
    <PortalHeading :title="$t('portal.nav.leads')" :subtitle="$t('leads.subtitle')" />
    <div class="mb-2 flex flex-wrap items-center gap-3">
      <FormField v-model="mode" as="select" class="w-full sm:w-56">
        <template #options>
          <option value="">{{ $t('directory.allModes') }}</option>
          <option v-for="m in modes" :key="m.name" :value="m.name">{{ $t(`modes.${m.code}.name`) }}</option>
        </template>
      </FormField>
      <label class="flex items-center gap-2 text-sm font-semibold text-ink-soft"><input v-model="onlyOpen" type="checkbox" class="size-4 accent-brand" /> {{ $t('leads.onlyOpen') }}</label>
    </div>
    <FilterTabs v-model="status" :options="tabs" class="mt-4" />
    <div v-if="loading === 'pending' && !data" class="grid gap-4 md:grid-cols-2"><div v-for="i in 4" :key="i" class="skeleton h-52" /></div>
    <TransitionGroup v-else-if="data?.items.length" tag="div" class="grid gap-4 md:grid-cols-2" enter-active-class="transition duration-500" enter-from-class="opacity-0 translate-y-3">
      <LeadCard v-for="r in data.items" :key="r.name" :r="r" />
    </TransitionGroup>
    <div v-else class="card"><EmptyState icon="inbox" :title="$t('leads.emptyTitle')" :text="$t('leads.emptyText')" /></div>
    <AppPagination v-if="data" v-model="page" class="mt-8" :total="data.total" :page-size="20" />
  </div>
</template>
