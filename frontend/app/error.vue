<script setup lang="ts">
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()
const notFound = computed(() => props.error.statusCode === 404)
useHead({ title: () => (notFound.value ? '404' : 'Error') })
</script>

<template>
  <div class="relative grid min-h-dvh place-items-center overflow-hidden bg-night-950 px-6 text-center text-white">
    <ChartBackground tone="night" />
    <div class="relative max-w-lg">
      <p class="font-display chart-em text-8xl !text-[#ef6b5b] sm:text-9xl">{{ error.statusCode }}</p>
      <h1 class="font-display mt-6 text-3xl sm:text-4xl">{{ notFound ? $t('errors.notFoundTitle') : $t('errors.serverTitle') }}</h1>
      <p class="mt-3 text-white/65">{{ notFound ? $t('errors.notFoundText') : $t('errors.serverText') }}</p>
      <div class="mt-8 flex flex-wrap justify-center gap-3">
        <AppButton variant="accent" icon="arrow-left" @click="clearError({ redirect: '/' })">{{ $t('errors.backHome') }}</AppButton>
        <AppButton to="/get-quote" variant="night">{{ $t('nav.getQuote') }}</AppButton>
      </div>
    </div>
  </div>
</template>
