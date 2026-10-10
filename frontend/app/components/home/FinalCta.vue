<script setup lang="ts">
/** Closing invitation beside a ship under way. */
const frame = ref<HTMLElement | null>(null)
useParallax(frame, 40)
</script>

<template>
  <section class="relative overflow-hidden border-t border-line px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
    <ChartBackground :density="10" />
    <div class="relative mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-2">
      <div v-reveal class="text-center lg:text-start">
        <h2 class="font-display text-4xl leading-tight text-ink sm:text-5xl">
          {{ $t('home.final.title1') }} <span class="chart-em">{{ $t('home.final.title2') }}</span>
        </h2>
        <p class="mt-5 text-lg text-muted">{{ $t('home.final.subtitle') }}</p>
        <div class="mt-9 flex flex-col justify-center gap-3 sm:flex-row lg:justify-start">
          <AppButton to="/get-quote" variant="accent" size="lg" icon-end="arrow-right">{{ $t('nav.getQuoteFree') }}</AppButton>
          <AppButton to="/register/forwarder" variant="secondary" size="lg">{{ $t('home.final.forwarder') }}</AppButton>
        </div>
      </div>
      <div ref="frame" v-reveal="120" class="photo-wipe relative overflow-hidden rounded-3xl shadow-2xl">
        <ChartPhoto name="cranes" :alt="$t('photos.cranes')" sizes="(min-width: 1024px) 600px, 100vw" class="parallax-layer aspect-[4/3]" />
        <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-night-950/50 to-transparent" />
        <p class="chart-label absolute start-5 bottom-5 rounded-full bg-night-950/55 px-2.5 py-1 text-white backdrop-blur">{{ $t('home.final.photoLabel') }}</p>
      </div>
    </div>
  </section>
</template>
