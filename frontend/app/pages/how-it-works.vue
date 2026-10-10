<script setup lang="ts">
const { t } = useI18n()
usePageSeo({ title: t('how.seoTitle'), description: t('how.seoDescription') })
useBreadcrumbs([{ name: t('nav.home'), item: '/' }, { name: t('nav.howItWorks'), item: '/how-it-works' }])

const details = [
  { icon: 'file-text', key: 'd1' },
  { icon: 'send', key: 'd2' },
  { icon: 'scale', key: 'd3' },
  { icon: 'handshake', key: 'd4' },
  { icon: 'star', key: 'd5' },
]
</script>

<template>
  <div>
    <PageHero :eyebrow="$t('nav.howItWorks')" :title="$t('how.title')" :subtitle="$t('how.subtitle')">
      <AppButton to="/get-quote" variant="accent" size="lg" icon-end="arrow-right">{{ $t('nav.getQuoteFree') }}</AppButton>
    </PageHero>

    <HowItWorks />

    <section class="mx-auto max-w-4xl px-4 pb-24 sm:px-6 lg:px-8">
      <SectionHeading :title="$t('how.detailTitle')" />
      <ol class="relative mt-14 space-y-10 border-s-2 border-dashed border-line-strong ps-10">
        <li v-for="(d, i) in details" :key="d.key" v-reveal="i * 60" class="relative">
          <span class="absolute -start-[3.35rem] grid size-11 place-items-center rounded-2xl bg-night-900 text-white shadow-lg">
            <AppIcon :name="d.icon" :size="20" />
          </span>
          <h3 class="text-xl font-bold">{{ $t(`how.${d.key}.title`) }}</h3>
          <p class="mt-2 leading-relaxed text-muted">{{ $t(`how.${d.key}.text`) }}</p>
        </li>
      </ol>
    </section>

    <ForwarderBand />
    <FinalCta />
  </div>
</template>
