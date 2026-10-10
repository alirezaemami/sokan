<script setup lang="ts">
const { t } = useI18n()
usePageSeo({ title: t('legal.terms.title'), description: t('legal.terms.intro') })
const SECTIONS = 5
</script>

<template>
  <div>
    <PageHero compact :title="$t('legal.terms.title')" :subtitle="$t('legal.updated')" />
    <article class="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
      <p class="text-lg leading-relaxed text-ink-soft">{{ $t('legal.terms.intro') }}</p>
      <section v-for="i in SECTIONS" :key="i" class="mt-10">
        <h2 class="text-xl font-bold">{{ $t(`legal.terms.s${i}.title`) }}</h2>
        <p class="mt-3 leading-relaxed text-muted">{{ $t(`legal.terms.s${i}.text`) }}</p>
      </section>
    </article>
  </div>
</template>
