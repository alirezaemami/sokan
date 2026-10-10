<script setup lang="ts">
const { t } = useI18n()
usePageSeo({ title: t('faq.seoTitle'), description: t('faq.seoDescription') })
useBreadcrumbs([{ name: t('nav.home'), item: '/' }, { name: t('nav.faq'), item: '/faq' }])
</script>

<template>
  <div>
    <PageHero compact :eyebrow="$t('faq.eyebrow')" :title="$t('faq.title')" />
    <section class="px-4 py-16 sm:px-6 lg:px-8">
      <h2 class="mx-auto mb-6 max-w-3xl text-xl font-bold">{{ $t('faq.shippers') }}</h2>
      <FaqSection group="faq.general" :count="6" />
      <h2 class="mx-auto mt-16 mb-6 max-w-3xl text-xl font-bold">{{ $t('faq.forwarders.title') }}</h2>
      <FaqSection group="faq.forwarders" :count="5" />
    </section>
    <FinalCta />
  </div>
</template>
