<script setup lang="ts">
const { t } = useI18n()
usePageSeo({ title: t('about.seoTitle'), description: t('about.subtitle') })
useBreadcrumbs([{ name: t('nav.home'), item: '/' }, { name: t('nav.about'), item: '/about' }])
const values = [
  { icon: 'scale', key: 'v1' },
  { icon: 'shield-check', key: 'v2' },
  { icon: 'handshake', key: 'v3' },
]
</script>

<template>
  <div>
    <PageHero :eyebrow="$t('nav.about')" :title="$t('about.title')" :subtitle="$t('about.subtitle')" />
    <section class="mx-auto grid max-w-6xl items-center gap-14 px-4 py-20 sm:px-6 lg:grid-cols-2 lg:px-8">
      <div v-reveal>
        <h2 class="text-3xl font-extrabold">{{ $t('about.storyTitle') }}</h2>
        <p class="mt-5 leading-relaxed text-muted">{{ $t('about.story1') }}</p>
        <p class="mt-4 leading-relaxed text-muted">{{ $t('about.story2') }}</p>
      </div>
      <div v-reveal="120" class="relative mx-auto w-full max-w-md rounded-[2rem] bg-night-950 p-8">
        <AuroraBackground :grid="false" />
        <RouteGlobe class="relative" />
      </div>
    </section>
    <section class="mx-auto max-w-6xl px-4 pb-24 sm:px-6 lg:px-8">
      <div class="grid gap-4 md:grid-cols-3">
        <div v-for="(v, i) in values" :key="v.key" v-reveal="i * 90" class="card p-7">
          <AppIcon :name="v.icon" :size="26" class="text-brand" />
          <h3 class="mt-4 text-lg font-bold">{{ $t(`about.${v.key}.title`) }}</h3>
          <p class="mt-2 text-sm leading-relaxed text-muted">{{ $t(`about.${v.key}.text`) }}</p>
        </div>
      </div>
    </section>
    <FinalCta />
  </div>
</template>
