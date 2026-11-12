<script setup lang="ts">
/**
 * Four facts under the hero, read from app.config (`home.stats`) so they can
 * be swapped for real network numbers without touching this component.
 */
const props = defineProps<{ modeCount: number }>()
const config = useAppConfig()

const items = computed(() =>
  config.home.stats.map((s) => ({
    ...s,
    value: s.value === 'modes' ? props.modeCount || s.fallback || 0 : s.value,
  })),
)
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
        <dd v-if="it.icon" class="mt-3 flex items-start gap-3 text-ink">
          <AppIcon :name="it.icon" :size="30" class="shrink-0 text-sea" />
          <span v-if="it.textKey" class="text-sm leading-snug text-ink-soft">{{ $t(it.textKey) }}</span>
        </dd>
        <dd v-else class="font-display mt-3 text-4xl text-ink sm:text-5xl">
          <template v-if="it.text">{{ it.text }}</template>
          <CountUp v-else :to="Number(it.value) || 0" :suffix="it.suffix || ''" />
        </dd>
      </div>
    </dl>
  </section>
</template>
