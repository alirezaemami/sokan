<script setup lang="ts">
import type { TransportMode } from '~/types/sokan'

defineProps<{ modes: TransportMode[] }>()
const localePath = useLocalePath()
</script>

<template>
  <section class="relative overflow-hidden bg-sunken/60 py-24">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <SectionHeading :eyebrow="$t('home.modes.eyebrow')" :title="$t('home.modes.title')" :subtitle="$t('home.modes.subtitle')" />
      <div class="mt-14 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <TiltCard v-for="(m, i) in modes" :key="m.name" v-reveal="(i % 4) * 70" class="rounded-2xl">
          <NuxtLink
            :to="{ path: localePath('/get-quote'), query: { mode: m.name } }"
            class="card group flex h-full flex-col p-5 transition-all duration-300 hover:border-brand/40 sm:p-6"
          >
            <span class="grid size-12 place-items-center rounded-2xl bg-brand/10 text-brand transition-all duration-500 group-hover:scale-110 group-hover:rotate-[-6deg] group-hover:bg-brand-gradient group-hover:text-white">
              <AppIcon :name="m.icon" :size="24" />
            </span>
            <h3 class="mt-5 font-bold sm:text-lg">{{ $t(`modes.${m.code}.name`) }}</h3>
            <p class="mt-1.5 line-clamp-3 text-xs leading-relaxed text-muted sm:text-sm">{{ $t(`modes.${m.code}.desc`) }}</p>
            <span class="mt-auto inline-flex items-center gap-1 pt-4 text-sm font-semibold text-brand opacity-0 transition-all duration-300 group-hover:opacity-100">
              {{ $t('home.modes.quote') }} <AppIcon name="arrow-right" :size="14" flip />
            </span>
          </NuxtLink>
        </TiltCard>
      </div>
    </div>
  </section>
</template>
