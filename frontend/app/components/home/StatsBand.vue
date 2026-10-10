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
        { value: s.forwarders, suffix: '+', key: 'home.stats.forwarders' },
        { value: s.requests, suffix: '+', key: 'home.stats.requests' },
        { value: s.quotes, suffix: '+', key: 'home.stats.quotes' },
        { value: s.countries, suffix: '', key: 'home.stats.countries' },
      ]
    : [
        { value: 0, suffix: '', key: 'home.stats.costForShippers', text: '$0' },
        { value: props.modeCount || 8, suffix: '', key: 'home.stats.modes' },
        { value: 24, suffix: '/7', key: 'home.stats.alwaysOn' },
        { value: 100, suffix: '%', key: 'home.stats.private' },
      ]
})
</script>

<template>
  <section class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
    <dl class="grid grid-cols-2 border-y border-line-strong lg:grid-cols-4">
      <div
        v-for="(it, i) in items"
        :key="it.key"
        v-reveal="i * 80"
        class="border-line px-4 py-7 sm:px-6"
        :class="[i % 2 === 0 && 'border-e', i < 2 && 'border-b lg:border-b-0', i === 1 && 'lg:border-e', i === 2 && 'lg:border-e']"
      >
        <dt class="chart-label text-muted">{{ $t(it.key) }}</dt>
        <dd class="font-display mt-3 text-4xl text-ink sm:text-5xl">
          <template v-if="it.text">{{ it.text }}</template>
          <CountUp v-else :to="it.value" :suffix="it.suffix" />
        </dd>
      </div>
    </dl>
  </section>
</template>
