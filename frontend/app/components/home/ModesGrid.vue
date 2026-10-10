<script setup lang="ts">
import type { TransportMode } from '~/types/sokan'
import { MODE_PHOTOS } from '~/utils/photos'

/** One photo card per transport mode; each opens the request form pre-set to that mode. */
defineProps<{ modes: TransportMode[] }>()
const localePath = useLocalePath()
</script>

<template>
  <section class="relative overflow-hidden border-y border-line bg-sunken/50 py-20 lg:py-24">
    <ChartBackground :density="10" />
    <div class="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <SectionHeading :eyebrow="$t('home.modes.eyebrow')" :title="$t('home.modes.title')" :subtitle="$t('home.modes.subtitle')" />
      <div class="mt-14 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <NuxtLink
          v-for="(m, i) in modes"
          :key="m.name"
          :to="{ path: localePath('/get-quote'), query: { mode: m.name } }"
          class="card group flex flex-col overflow-hidden p-0 transition-[translate,border-color,box-shadow] duration-300 hover:-translate-y-1 hover:border-sea/50 hover:shadow-xl"
        >
          <div v-reveal="(i % 4) * 90" class="photo-wipe relative">
            <ChartPhoto
              :name="MODE_PHOTOS[m.code] || 'port'"
              :alt="$t(`photos.${MODE_PHOTOS[m.code] || 'port'}`)"
              sizes="(min-width: 1024px) 300px, 50vw"
              class="aspect-[4/3]"
              img-class="transition-transform duration-[1.2s] ease-[var(--ease-spring)] group-hover:scale-110"
            />
            <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-night-950/55 to-transparent" />
            <span class="absolute start-3 bottom-3 grid size-10 place-items-center rounded-full bg-surface/90 text-ink shadow-md backdrop-blur transition-colors duration-500 group-hover:bg-buoy group-hover:text-white">
              <AppIcon :name="m.icon" :size="18" />
            </span>
            <span class="chart-label absolute end-3 top-3 rounded-full bg-night-950/55 px-2 py-0.5 text-white backdrop-blur">{{ $t(`modes.${m.code}.category`) }}</span>
          </div>
          <div class="flex flex-1 flex-col p-4 sm:p-5">
            <h3 class="font-semibold sm:text-lg">{{ $t(`modes.${m.code}.name`) }}</h3>
            <p class="mt-1.5 line-clamp-3 text-xs leading-relaxed text-muted sm:text-sm">{{ $t(`modes.${m.code}.desc`) }}</p>
            <span class="mt-auto inline-flex items-center gap-1 pt-4 text-sm font-semibold text-sea">
              {{ $t('home.modes.quote') }} <AppIcon name="arrow-right" :size="14" flip class="transition-transform group-hover:translate-x-1 rtl:group-hover:-translate-x-1" />
            </span>
          </div>
        </NuxtLink>
      </div>
    </div>
  </section>
</template>
