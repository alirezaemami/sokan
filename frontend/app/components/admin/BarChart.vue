<script setup lang="ts">
/**
 * Bar chart drawn with plain boxes, so it is responsive, RTL-aware and
 * readable without a chart library. One or two series; the second is drawn
 * as a thinner buoy-red bar beside the first.
 */
const props = withDefaults(
  defineProps<{
    data: { label: string; values: number[] }[]
    series: string[]
    format?: (v: number) => string
    height?: number
    /** Show every nth x label; the rest stay as hover tooltips. */
    labelEvery?: number
  }>(),
  { height: 180, labelEvery: 1 },
)

const fmt = useFormat()
const show = (v: number) => (props.format ? props.format(v) : fmt.number(v))

// Round the top of the scale up to a tidy number so gridlines read well.
const empty = computed(() => !props.data.some((d) => d.values.some((v) => v > 0)))
const max = computed(() => {
  const m = Math.max(0, ...props.data.flatMap((d) => d.values))
  if (m <= 0) return 2
  const p = 10 ** Math.floor(Math.log10(m))
  const top = Math.ceil(m / p) * p
  // Keep the middle gridline on a whole number (2 → 1, not 1 → 0.5).
  return top < 10 && top % 2 ? top + 1 : top
})
const ticks = computed(() => [1, 0.5, 0].map((f) => max.value * f))
const tones = ['bg-sea', 'bg-buoy']
const swatches = ['bg-sea', 'bg-buoy']
</script>

<template>
  <figure class="min-w-0">
    <figcaption v-if="series.length > 1" class="mb-3 flex flex-wrap gap-4 text-xs text-muted">
      <span v-for="(s, i) in series" :key="s" class="inline-flex items-center gap-1.5"><span class="size-2.5 rounded-sm" :class="swatches[i]" />{{ s }}</span>
    </figcaption>
    <div class="flex gap-2">
      <!-- y axis -->
      <div class="flex shrink-0 flex-col justify-between text-end font-mono text-[0.625rem] text-faint tabular-nums" :style="{ height: `${height}px` }">
        <span v-for="t in ticks" :key="t" class="-my-1.5">{{ show(t) }}</span>
      </div>
      <div class="relative min-w-0 flex-1">
        <div class="absolute inset-x-0 top-0 flex flex-col justify-between" :style="{ height: `${height}px` }" aria-hidden="true">
          <span v-for="t in ticks" :key="t" class="border-t border-dashed border-line" />
        </div>
        <p v-if="empty" class="absolute inset-x-0 top-1/2 -translate-y-1/2 text-center text-sm text-faint">{{ $t('admin.chartEmpty') }}</p>
        <div class="relative flex items-end gap-[3%]" :style="{ height: `${height}px` }">
          <div v-for="d in data" :key="d.label" class="group relative flex h-full min-w-0 flex-1 items-end justify-center gap-[12%]">
            <span
              v-for="(v, i) in d.values"
              :key="i"
              class="rounded-t-[3px] transition-[height] duration-500"
              :class="[tones[i], i === 0 ? 'w-full max-w-7' : 'w-1/2 max-w-3']"
              :style="{ height: `${(v / max) * 100}%`, minHeight: v > 0 ? '2px' : '0' }"
            />
            <!-- tooltip -->
            <span class="pointer-events-none absolute bottom-full z-10 mb-2 hidden whitespace-nowrap rounded-lg bg-helm px-2 py-1 text-xs text-helm-ink shadow-lg group-hover:block">
              <b class="font-semibold">{{ d.label }}</b>
              <span v-for="(v, i) in d.values" :key="i" class="block tabular-nums">{{ series[i] }}: {{ show(v) }}</span>
            </span>
          </div>
        </div>
        <div class="mt-2 flex gap-[3%] overflow-hidden text-center font-mono text-[0.625rem] text-faint">
          <!-- A label is wider than its column: centre it under the bar and let the row clip the ends. -->
          <span v-for="(d, i) in data" :key="d.label" class="relative h-4 min-w-0 flex-1">
            <span v-if="i % labelEvery === 0" class="absolute start-1/2 -translate-x-1/2 whitespace-nowrap rtl:translate-x-1/2">{{ d.label }}</span>
          </span>
        </div>
      </div>
    </div>
  </figure>
</template>
