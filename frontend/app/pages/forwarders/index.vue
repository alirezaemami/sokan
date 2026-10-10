<script setup lang="ts">
/**
 * Public forwarder directory. Filters live in the query string so every
 * filtered view is a shareable, crawlable URL.
 */
const api = useSokan()
const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { modes, load } = useModes()
await useAsyncData('modes', load)

const search = ref((route.query.q as string) || '')
const mode = ref((route.query.mode as string) || '')
const country = ref<string | null>((route.query.country as string) || null)
const page = ref(Number(route.query.page) || 1)
const PAGE_SIZE = 12

const params = computed(() => ({
  search: (route.query.q as string) || undefined,
  mode: (route.query.mode as string) || undefined,
  country: (route.query.country as string) || undefined,
  page: Number(route.query.page) || 1,
  page_size: PAGE_SIZE,
}))

const { data, status } = await useAsyncData('forwarders', () => api.forwarders(params.value), { watch: [params] })

function apply() {
  router.replace({ query: { q: search.value || undefined, mode: mode.value || undefined, country: country.value || undefined } })
  page.value = 1
}
watchDebounced(search, apply, { debounce: 350 })
watch([mode, country], apply)
watch(page, (p) => router.replace({ query: { ...route.query, page: p > 1 ? p : undefined } }))

usePageSeo({ title: t('directory.seoTitle'), description: t('directory.seoDescription') })
useBreadcrumbs([{ name: t('nav.home'), item: '/' }, { name: t('nav.forwarders'), item: '/forwarders' }])
</script>

<template>
  <div>
    <PageHero compact :eyebrow="$t('directory.eyebrow')" :title="$t('directory.title')" :subtitle="$t('directory.subtitle')" />

    <section class="mx-auto -mt-8 max-w-7xl px-4 pb-24 sm:px-6 lg:px-8">
      <div class="glass relative z-10 grid gap-3 rounded-3xl p-3 shadow-xl sm:grid-cols-[1.4fr_1fr_1fr] sm:p-4">
        <FormField v-model="search" icon="search" type="search" :placeholder="$t('directory.searchPlaceholder')" />
        <FormField v-model="mode" as="select">
          <template #options>
            <option value="">{{ $t('directory.allModes') }}</option>
            <option v-for="m in modes" :key="m.name" :value="m.name">{{ $t(`modes.${m.code}.name`) }}</option>
          </template>
        </FormField>
        <ClientOnly><CountrySelect v-model="country" :placeholder="$t('directory.anyCountry')" /></ClientOnly>
      </div>

      <p class="mt-8 text-sm text-muted">{{ $t('directory.count', { n: data?.total ?? 0 }) }}</p>

      <div v-if="status === 'pending' && !data" class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="i in 6" :key="i" class="skeleton h-52" />
      </div>
      <div v-else-if="data?.items.length" class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <ForwarderTile v-for="(f, i) in data.items" :key="f.name" v-reveal="(i % 3) * 60" :f="f" />
      </div>
      <div v-else class="card mt-6">
        <EmptyState icon="search" :title="$t('directory.emptyTitle')" :text="$t('directory.emptyText')">
          <AppButton to="/get-quote" variant="primary" icon-end="arrow-right">{{ $t('directory.emptyCta') }}</AppButton>
        </EmptyState>
      </div>

      <AppPagination v-if="data" v-model="page" class="mt-10" :total="data.total" :page-size="PAGE_SIZE" />

      <div class="card mt-16 flex flex-col items-center justify-between gap-6 p-8 text-center sm:flex-row sm:text-start">
        <div>
          <h2 class="text-xl font-bold">{{ $t('directory.joinTitle') }}</h2>
          <p class="mt-1 text-muted">{{ $t('directory.joinText') }}</p>
        </div>
        <AppButton to="/register/forwarder" variant="primary" icon-end="arrow-right">{{ $t('home.forwarders.cta') }}</AppButton>
      </div>
    </section>
  </div>
</template>
