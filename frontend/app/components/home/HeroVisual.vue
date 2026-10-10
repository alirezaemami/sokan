<script setup lang="ts">
/**
 * Product demo, not decoration: one request card, then forwarder quotes
 * arriving one after another with the best price highlighted. Purely
 * illustrative sample data — labelled as an example.
 */
const { t } = useI18n()
const fmt = useFormat()

const quotes = computed(() => [
  { name: 'Aster Logistics', price: 2860, days: '28–32', rating: 4.9, hue: 250, best: false },
  { name: 'BlueWake Freight', price: 2640, days: '30–34', rating: 4.8, hue: 190, best: true },
  { name: 'Kara Shipping', price: 2915, days: '26–29', rating: 4.7, hue: 15, best: false },
])

const shown = ref(3)
let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  shown.value = 0
  let step = 0
  timer = setInterval(() => {
    step = (step + 1) % 6
    shown.value = Math.min(step, 3)
  }, 1500)
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="relative mx-auto w-full max-w-[520px]">
    <RouteGlobe class="absolute -top-16 start-1/2 w-[125%] max-w-none -translate-x-1/2 opacity-70 rtl:translate-x-1/2" />

    <div class="relative space-y-3 pt-6">
      <!-- The request -->
      <div class="glass-dark animate-float rounded-3xl p-5 shadow-2xl shadow-brand/20">
        <div class="flex items-center justify-between gap-3">
          <span class="inline-flex items-center gap-2 rounded-full bg-lagoon/15 px-3 py-1 text-xs font-bold text-lagoon">
            <span class="relative flex size-2"><span class="animate-ping-slow absolute inline-flex size-full rounded-full bg-lagoon" /><span class="relative size-2 rounded-full bg-lagoon" /></span>
            {{ t('home.visual.live') }}
          </span>
          <span class="text-xs text-white/50">{{ t('home.visual.example') }}</span>
        </div>
        <div class="mt-4 flex items-center gap-3 text-white">
          <div class="min-w-0">
            <p class="text-xs text-white/50">{{ t('common.from') }}</p>
            <p class="truncate text-lg font-bold">{{ fmt.flag('CN') }} {{ t('home.visual.origin') }}</p>
          </div>
          <div class="relative mx-1 h-px flex-1 bg-gradient-to-r from-lagoon/0 via-lagoon to-lagoon/0">
            <AppIcon name="ship" :size="18" class="absolute -top-2.5 start-1/2 -translate-x-1/2 text-lagoon rtl:translate-x-1/2" />
          </div>
          <div class="min-w-0 text-end">
            <p class="text-xs text-white/50">{{ t('common.to') }}</p>
            <p class="truncate text-lg font-bold">{{ fmt.flag('DE') }} {{ t('home.visual.destination') }}</p>
          </div>
        </div>
        <div class="mt-4 flex flex-wrap gap-2 text-xs text-white/70">
          <span class="rounded-lg bg-white/8 px-2.5 py-1">2 × 40' HC</span>
          <span class="rounded-lg bg-white/8 px-2.5 py-1">{{ t('home.visual.commodity') }}</span>
          <span class="rounded-lg bg-white/8 px-2.5 py-1">FOB</span>
        </div>
      </div>

      <!-- Quotes arriving -->
      <TransitionGroup
        tag="div"
        class="space-y-2.5 ps-6"
        enter-active-class="transition duration-700 ease-[var(--ease-spring)]"
        enter-from-class="opacity-0 translate-y-6 scale-95"
        leave-active-class="transition duration-300"
        leave-to-class="opacity-0"
      >
        <div
          v-for="q in quotes.slice(0, shown)"
          :key="q.name"
          class="flex items-center gap-3 rounded-2xl p-3.5 text-white backdrop-blur-xl"
          :class="q.best ? 'bg-gradient-to-r from-brand/40 to-lagoon/25 ring-1 ring-lagoon/50' : 'bg-white/6 ring-1 ring-white/10'"
        >
          <span class="grid size-10 shrink-0 place-items-center rounded-xl text-sm font-bold" :style="{ background: `hsl(${q.hue} 70% 55%)` }">{{ q.name.charAt(0) }}</span>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-semibold">{{ q.name }}</p>
            <p class="text-xs text-white/55">★ {{ fmt.number(q.rating, 1) }} · {{ q.days }} {{ t('units.days') }}</p>
          </div>
          <div class="text-end">
            <p class="text-base font-extrabold tabular-nums">{{ fmt.money(q.price, 'USD') }}</p>
            <p v-if="q.best" class="text-[0.68rem] font-bold text-lagoon">{{ t('home.visual.best') }}</p>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>
