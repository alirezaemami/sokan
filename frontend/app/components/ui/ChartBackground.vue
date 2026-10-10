<script setup lang="ts">
/**
 * Depth contours with a few soundings — the ground of every Chart Room
 * surface. Pure SVG computed in setup, so it is server-rendered with the
 * page (no canvas, no JS on the client) and the swell drift is CSS only,
 * frozen under prefers-reduced-motion.
 */
const props = withDefaults(defineProps<{ tone?: 'paper' | 'night'; compass?: boolean; density?: number }>(), {
  tone: 'paper',
  compass: false,
  density: 16,
})

const W = 1440
const H = 900

// Deterministic contours: layered sine waves, so SSR and client agree.
const lines = computed(() =>
  Array.from({ length: props.density }, (_, k) => {
    const base = 30 + k * (H / props.density)
    let d = ''
    for (let x = -40; x <= W + 40; x += 24) {
      const y = base + Math.sin(x / 150 + k * 0.72) * 26 + Math.sin(x / 57 + k * 1.3) * 7
      d += `${x === -40 ? 'M' : 'L'}${x} ${y.toFixed(1)}`
    }
    return d
  }),
)

const soundings = [
  [140, 160, '12'], [410, 300, '27'], [690, 120, '34'], [980, 380, '48'], [1260, 220, '55'],
  [260, 620, '19'], [620, 700, '41'], [1120, 640, '63'], [860, 540, '38'],
] as const
</script>

<template>
  <div class="pointer-events-none absolute inset-0 overflow-hidden" :class="tone === 'night' ? 'text-tide/15' : 'text-contour'" aria-hidden="true">
    <svg class="animate-swell absolute -inset-[4%] h-[108%] w-[108%]" :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="xMidYMid slice" fill="none">
      <path v-for="(d, i) in lines" :key="i" :d="d" stroke="currentColor" :stroke-width="i % 4 === 0 ? 1.4 : 0.9" />
      <g fill="currentColor" font-family="Martian Mono, monospace" font-size="11">
        <text v-for="([x, y, t], i) in soundings" :key="`s${i}`" :x="x" :y="y">{{ t }}</text>
      </g>
    </svg>

    <!-- Compass rose, top end corner -->
    <svg v-if="compass" class="absolute -top-10 end-[-40px] size-56 opacity-70 sm:size-72" viewBox="0 0 200 200" fill="none" stroke="currentColor">
      <circle cx="100" cy="100" r="88" stroke-width="1" />
      <circle cx="100" cy="100" r="70" stroke-width="0.6" stroke-dasharray="2 4" />
      <path d="M100 8 L108 100 L100 192 L92 100 Z M8 100 L100 92 L192 100 L100 108 Z" stroke-width="1" />
      <path d="M35 35 L104 96 L165 165 L96 104 Z M165 35 L104 104 L35 165 L96 96 Z" stroke-width="0.6" />
      <text x="96" y="24" font-family="Martian Mono, monospace" font-size="11" fill="currentColor" stroke="none">N</text>
    </svg>
  </div>
</template>
