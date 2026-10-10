<script setup lang="ts">
const { t } = useI18n()
const { modes, load } = useModes()
await useAsyncData('modes', load)

usePageSeo({ title: t('wizard.seoTitle'), description: t('wizard.seoDescription') })
useBreadcrumbs([{ name: t('nav.home'), item: '/' }, { name: t('nav.getQuote'), item: '/get-quote' }])
</script>

<template>
  <div>
    <PageHero compact :eyebrow="$t('wizard.eyebrow')" :title="$t('wizard.title')" :subtitle="$t('wizard.subtitle')" />
    <section class="mx-auto max-w-6xl px-4 pt-4 pb-20 sm:px-6 lg:px-8">
      <ClientOnly>
        <RequestWizard :modes="modes" />
        <template #fallback>
          <div class="space-y-4">
            <div class="skeleton h-3 w-full" />
            <div class="skeleton h-10 w-1/2" />
            <div class="grid grid-cols-4 gap-3"><div v-for="i in 8" :key="i" class="skeleton h-24" /></div>
          </div>
        </template>
      </ClientOnly>
    </section>
  </div>
</template>
