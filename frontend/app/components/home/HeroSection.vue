<script setup lang="ts">
import type { TransportMode } from '~/types/sokan'

/**
 * The home page's first screen: one sentence and one search bar, like
 * booking a flight. Mode, from and to land in the request form pre-filled.
 */
defineProps<{ modes: TransportMode[] }>()
</script>

<template>
  <!-- Clip only sideways: the country lists must be free to drop below the hero. -->
  <section class="relative z-10 overflow-x-clip pt-[72px]">
    <ChartBackground :density="8" />
    <div class="relative mx-auto max-w-5xl px-4 pt-14 pb-16 text-center sm:px-6 lg:pt-24 lg:pb-24">
      <p class="rise inline-flex items-center gap-2 rounded-full bg-starboard/10 px-3.5 py-1.5 text-sm font-semibold text-starboard">
        <AppIcon name="circle-check" :size="16" /> {{ $t('home.hero.eyebrow') }}
      </p>
      <h1 class="rise font-display mx-auto mt-6 max-w-4xl text-[2.4rem] leading-[1.08] text-balance text-ink sm:text-5xl lg:text-6xl" style="--d: 60ms">
        {{ $t('home.hero.title') }}
      </h1>
      <p class="rise mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-muted" style="--d: 120ms">{{ $t('home.hero.subtitle') }}</p>

      <div class="rise card relative z-20 mx-auto mt-10 max-w-4xl p-2.5 text-start shadow-xl sm:p-3" style="--d: 180ms">
        <HeroQuoteBar :modes="modes" />
      </div>

      <ul class="rise mt-6 flex flex-wrap justify-center gap-x-6 gap-y-2 text-sm text-ink-soft" style="--d: 240ms">
        <li v-for="k in ['trust1', 'trust2', 'trust3']" :key="k" class="flex items-center gap-2">
          <AppIcon name="circle-check" :size="16" class="text-starboard" /> {{ $t(`home.hero.${k}`) }}
        </li>
      </ul>
      <NuxtLinkLocale to="/for-forwarders" class="rise mt-8 inline-flex items-center gap-1.5 text-sm font-semibold text-sea" style="--d: 300ms">
        {{ $t('home.hero.forwarderLink') }} <AppIcon name="arrow-right" :size="15" flip />
      </NuxtLinkLocale>
    </div>
  </section>
</template>
