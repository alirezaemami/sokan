<script setup lang="ts">
const api = useSokan()
const { t } = useI18n()
const { modes: modeCache } = useModes()
const config = useAppConfig()

const { data } = await useAsyncData('home', () => api.home())

const modes = computed(() => data.value?.modes ?? [])
// Verified, public providers only; the section waits until there are enough to look like a network.
const featured = computed(() => data.value?.featured ?? [])
const showFeatured = computed(() => featured.value.length >= config.home.featuredMinProviders)
watchEffect(() => {
  if (modes.value.length && !modeCache.value.length) modeCache.value = modes.value
})

usePageSeo({ title: t('seo.homeTitle'), description: t('seo.homeDescription') })
useSchemaOrg([
  defineWebSite({ name: 'Sokan' }),
  defineWebPage(),
])
</script>

<template>
  <div>
    <HeroSection :modes="modes" />
    <LiveTicker :live="data?.live ?? []" />
    <StatsBand :mode-count="modes.length" />
    <HowItWorks />
    <ModesGrid v-if="modes.length" :modes="modes" />
    <StorySection />
    <FeatureBento />

    <section v-if="showFeatured" class="mx-auto max-w-7xl px-4 pb-24 sm:px-6 lg:px-8">
      <div class="flex flex-wrap items-end justify-between gap-6">
        <SectionHeading align="start" :eyebrow="$t('home.featured.eyebrow')" :title="$t('home.featured.title')" />
        <AppButton to="/forwarders" variant="secondary" icon-end="arrow-right">{{ $t('common.viewAll') }}</AppButton>
      </div>
      <div class="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <ForwarderTile v-for="(f, i) in featured" :key="f.name" v-reveal="(i % 4) * 70" :f="f" />
      </div>
    </section>

    <TrustContact />

    <ForwarderBand />

    <section class="px-4 py-24 sm:px-6 lg:px-8">
      <SectionHeading :eyebrow="$t('faq.eyebrow')" :title="$t('faq.title')" />
      <div class="mt-12"><FaqSection group="faq.general" :count="6" /></div>
    </section>

    <FinalCta />
  </div>
</template>
