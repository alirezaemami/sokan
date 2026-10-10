<script setup lang="ts">
import type { TransportMode } from '~/types/sokan'

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
          v-reveal="(i % 4) * 70"
          :to="{ path: localePath('/get-quote'), query: { mode: m.name } }"
          class="card group flex flex-col p-5 transition-all duration-300 hover:-translate-y-1 hover:border-sea/50 sm:p-6"
        >
          <div class="flex items-start justify-between gap-2">
            <span class="grid size-11 place-items-center rounded-full border border-line-strong text-ink transition-all duration-500 group-hover:border-helm group-hover:bg-helm group-hover:text-helm-ink">
              <AppIcon :name="m.icon" :size="20" />
            </span>
            <span class="chart-label text-faint">{{ $t(`modes.${m.code}.category`) }}</span>
          </div>
          <h3 class="mt-5 font-semibold sm:text-lg">{{ $t(`modes.${m.code}.name`) }}</h3>
          <p class="mt-1.5 line-clamp-3 text-xs leading-relaxed text-muted sm:text-sm">{{ $t(`modes.${m.code}.desc`) }}</p>
          <span class="mt-auto inline-flex items-center gap-1 pt-4 text-sm font-semibold text-sea">
            {{ $t('home.modes.quote') }} <AppIcon name="arrow-right" :size="14" flip class="transition-transform group-hover:translate-x-1 rtl:group-hover:-translate-x-1" />
          </span>
        </NuxtLink>
      </div>
    </div>
  </section>
</template>
