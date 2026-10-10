<script setup lang="ts">
import type { HomePayload } from '~/types/sokan'

/**
 * Network numbers once they're impressive; until then, product facts. A
 * young marketplace showing "3 forwarders" would hurt more than help.
 */
const props = defineProps<{ stats: HomePayload['stats']; modeCount: number }>()

const items = computed(() => {
  const s = props.stats
  const mature = s.forwarders >= 25 && s.requests >= 100
  return mature
    ? [
        { value: s.forwarders, suffix: '+', key: 'home.stats.forwarders', icon: 'building' },
        { value: s.requests, suffix: '+', key: 'home.stats.requests', icon: 'send' },
        { value: s.quotes, suffix: '+', key: 'home.stats.quotes', icon: 'receipt' },
        { value: s.countries, suffix: '', key: 'home.stats.countries', icon: 'earth' },
      ]
    : [
        { value: 0, suffix: '', key: 'home.stats.costForShippers', icon: 'coins', text: '$0' },
        { value: props.modeCount || 8, suffix: '', key: 'home.stats.modes', icon: 'layers' },
        { value: 24, suffix: '/7', key: 'home.stats.alwaysOn', icon: 'clock' },
        { value: 100, suffix: '%', key: 'home.stats.private', icon: 'shield-check' },
      ]
})
</script>

<template>
  <section class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
    <div class="card grid grid-cols-2 divide-line overflow-hidden lg:grid-cols-4 lg:divide-x rtl:lg:divide-x-reverse">
      <div v-for="(it, i) in items" :key="it.key" v-reveal="i * 80" class="relative p-6 sm:p-8" :class="i < 2 && 'border-b border-line lg:border-b-0'">
        <AppIcon :name="it.icon" :size="22" class="text-brand" />
        <p class="mt-4 text-3xl font-extrabold tracking-tight sm:text-4xl">
          <template v-if="it.text">{{ it.text }}</template>
          <CountUp v-else :to="it.value" :suffix="it.suffix" />
        </p>
        <p class="mt-1 text-sm text-muted">{{ $t(it.key) }}</p>
      </div>
    </div>
  </section>
</template>
