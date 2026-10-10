<script setup lang="ts">
/**
 * Product demo, not decoration: a plotted voyage on a chart card, with
 * forwarder quotes logged underneath one after another, best price marked.
 * Sample data, labelled as an example.
 */
const { t } = useI18n()
const fmt = useFormat()

const quotes = [
  { name: 'Aster Logistics', price: 2860, days: '28–32', rating: 4.9, best: false },
  { name: 'BlueWake Freight', price: 2640, days: '30–34', rating: 4.8, best: true },
  { name: 'Kara Shipping', price: 2915, days: '26–29', rating: 4.7, best: false },
]

// SSR shows all three (complete at rest); the client replays the arrival.
const shown = ref(3)
let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  shown.value = 0
  let step = 0
  timer = setInterval(() => {
    step = (step + 1) % 7
    shown.value = Math.min(step, 3)
  }, 1400)
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="card relative mx-auto w-full max-w-[540px] overflow-hidden p-0">
    <div class="flex items-center justify-between gap-3 border-b border-line px-5 py-3">
      <span class="chart-label text-muted">{{ t('home.visual.voyage') }}</span>
      <span class="chart-label inline-flex items-center gap-1.5 text-starboard">
        <span class="relative flex size-2"><span class="animate-ping-slow absolute inline-flex size-full rounded-full bg-starboard" /><span class="relative size-2 rounded-full bg-starboard" /></span>
        {{ t('home.visual.live') }}
      </span>
    </div>

    <div class="relative bg-sunken/50 px-3 pt-2 pb-14" dir="ltr">
      <ChartMap />
      <!-- A chart is geography: labels sit physically beside their buoys and never mirror in RTL. -->
      <div class="absolute bottom-3 left-5 max-w-[48%] text-left" dir="auto">
        <p class="font-display text-lg leading-tight text-ink sm:text-xl">{{ fmt.flag('CN') }} {{ t('home.visual.origin') }}</p>
        <p class="chart-label mt-1 text-muted">2 × 40' HC · FOB</p>
      </div>
      <div class="absolute top-[30%] right-5 max-w-[48%] text-right" dir="auto">
        <p class="font-display text-lg leading-tight text-ink sm:text-xl">{{ t('home.visual.destination') }} {{ fmt.flag('DE') }}</p>
        <p class="chart-label mt-1 text-muted">{{ t('home.visual.commodity') }}</p>
      </div>
    </div>

    <div class="border-t border-line px-3 py-3">
      <p class="chart-label px-2 pb-2 text-faint">{{ t('home.visual.log') }}</p>
      <!-- All three slots are always laid out; quotes only fade in and out of
           their berth, so the card never changes height while it animates. -->
      <ul class="space-y-1.5">
        <li v-for="(q, i) in quotes" :key="q.name" class="relative rounded-xl border border-dashed border-line-strong">
          <div
            class="-m-px flex items-center gap-3 rounded-xl px-3 py-2.5 transition duration-500 ease-[var(--ease-spring)]"
            :class="[q.best ? 'bg-helm text-helm-ink' : 'bg-sunken', i < shown ? 'opacity-100' : 'translate-y-1.5 opacity-0']"
            :aria-hidden="i >= shown"
          >
            <span class="grid size-8 shrink-0 place-items-center rounded-full border text-xs font-semibold" :class="q.best ? 'border-helm-ink/30' : 'border-line-strong'">{{ q.name.charAt(0) }}</span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold">{{ q.name }}</p>
              <p class="text-xs opacity-70">★ {{ fmt.number(q.rating, 1) }} · {{ q.days }} {{ t('units.days') }}</p>
            </div>
            <div class="text-end">
              <p class="font-mono text-sm font-medium tabular-nums">{{ fmt.money(q.price, 'USD') }}</p>
              <!-- Buoy-red tag reads on the helm row in both themes. -->
              <p class="chart-label mt-1 rounded-full px-1.5 py-px" :class="q.best ? 'bg-buoy text-white' : 'invisible'">{{ t('home.visual.best') }}</p>
            </div>
          </div>
        </li>
      </ul>
    </div>
    <p class="chart-label border-t border-line px-5 py-2.5 text-faint">{{ t('home.visual.example') }}</p>
  </div>
</template>
