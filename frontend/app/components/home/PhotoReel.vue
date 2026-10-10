<script setup lang="ts">
/**
 * An endless, slow reel of freight photography, one frame per transport
 * mode, captioned like chart annotations. Pauses on hover; still under
 * reduced motion. The duplicate set exists only to make the loop seamless,
 * so it is hidden from assistive tech.
 */
import type { PhotoKey } from '~/utils/photos'

const frames: { photo: PhotoKey; mode: string }[] = [
  { photo: 'ship', mode: 'sea_fcl' },
  { photo: 'plane', mode: 'air' },
  { photo: 'train', mode: 'rail' },
  { photo: 'truck', mode: 'road_ftl' },
  { photo: 'cranes', mode: 'sea_lcl' },
  { photo: 'parcel', mode: 'courier' },
  { photo: 'highway', mode: 'road_ltl' },
  { photo: 'port', mode: 'project' },
]
</script>

<template>
  <section class="relative py-14 lg:py-20" :aria-label="$t('home.reel.title')">
    <div class="mx-auto mb-8 flex max-w-7xl flex-wrap items-end justify-between gap-4 px-4 sm:px-6 lg:px-8">
      <div v-reveal>
        <p class="chart-label text-sea">{{ $t('home.reel.eyebrow') }}</p>
        <h2 class="font-display mt-2 text-3xl text-ink sm:text-4xl">{{ $t('home.reel.title') }}</h2>
      </div>
      <p v-reveal="80" class="max-w-md text-muted">{{ $t('home.reel.subtitle') }}</p>
    </div>
    <div class="marquee-mask overflow-hidden">
      <ul class="marquee-track animate-marquee flex w-max gap-4" style="--marquee-duration: 70s">
        <template v-for="copy in 2" :key="copy">
          <li
            v-for="f in frames"
            :key="`${copy}-${f.photo}`"
            class="group relative w-64 shrink-0 overflow-hidden rounded-2xl sm:w-80"
            :aria-hidden="copy === 2 || undefined"
          >
            <ChartPhoto
              :name="f.photo"
              :alt="copy === 1 ? $t(`photos.${f.photo}`) : ''"
              sizes="(min-width: 640px) 320px, 256px"
              class="aspect-[4/5]"
              img-class="transition-transform duration-[1.2s] ease-[var(--ease-spring)] group-hover:scale-110"
            />
            <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-night-950/85 via-night-950/10 to-transparent" />
            <div class="absolute inset-x-0 bottom-0 p-4 text-white">
              <p class="chart-label text-tide">{{ $t(`modes.${f.mode}.category`) }}</p>
              <p class="font-display mt-1 text-2xl leading-tight">{{ $t(`modes.${f.mode}.name`) }}</p>
            </div>
          </li>
        </template>
      </ul>
    </div>
  </section>
</template>
