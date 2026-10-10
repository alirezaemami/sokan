<script setup lang="ts">
const { t } = useI18n()
usePageSeo({ title: t('legal.privacy.title'), description: t('legal.privacy.intro') })
const SECTIONS = 5
</script>

<template>
  <div>
    <PageHero compact :title="$t('legal.privacy.title')" :subtitle="$t('legal.updated')" />
    <article class="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
      <p class="text-lg leading-relaxed text-ink-soft">{{ $t('legal.privacy.intro') }}</p>
      <section v-for="i in SECTIONS" :key="i" class="mt-10">
        <h2 class="text-xl font-bold">{{ $t(`legal.privacy.s${i}.title`) }}</h2>
        <p class="mt-3 leading-relaxed text-muted">{{ $t(`legal.privacy.s${i}.text`) }}</p>
      </section>
    </article>
  </div>
</template>
