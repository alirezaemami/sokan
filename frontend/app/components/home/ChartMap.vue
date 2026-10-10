<script setup lang="ts">
/**
 * A plotted voyage on a chart: origin buoy (port red), destination buoy
 * (starboard green), real coordinates, and a route that draws itself while
 * a vessel follows it. Server-rendered SVG; all motion is CSS.
 */
withDefaults(defineProps<{ tone?: 'paper' | 'night' }>(), { tone: 'paper' })

// Shanghai → Hamburg, the example voyage used across the site.
const ROUTE = 'M56 236 C 150 236, 170 120, 262 104 S 392 70, 448 52'
</script>

<template>
  <svg
    viewBox="0 0 500 290"
    fill="none"
    class="w-full"
    :class="tone === 'night' ? 'text-tide' : 'text-ink'"
    role="img"
    :aria-label="$t('home.visual.mapLabel')"
  >
    <!-- Latitude / longitude grid -->
    <g stroke="currentColor" stroke-opacity=".12" stroke-width="1">
      <path v-for="x in [100, 200, 300, 400]" :key="`x${x}`" :d="`M${x} 10 V280`" />
      <path v-for="y in [70, 145, 220]" :key="`y${y}`" :d="`M10 ${y} H490`" />
    </g>
    <g fill="currentColor" fill-opacity=".45" font-family="Martian Mono, monospace" font-size="9">
      <text x="104" y="22">120°E</text><text x="404" y="22">10°E</text><text x="14" y="66">50°N</text><text x="14" y="216">30°N</text>
    </g>

    <!-- Route: faint full track, then the plotted line drawing over it -->
    <path :d="ROUTE" stroke="currentColor" stroke-opacity=".18" stroke-width="2" stroke-dasharray="3 6" />
    <path :d="ROUTE" class="plot" style="--len: 470; --d: 400ms" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" />

    <!-- Vessel -->
    <g class="vessel" :style="{ offsetPath: `path('${ROUTE}')` }">
      <circle r="9" class="fill-sea" fill-opacity=".18" />
      <path d="M-6 -2 L4 -2 L7 0 L4 2 L-6 2 Z" class="fill-sea" />
    </g>

    <!-- Origin buoy -->
    <g transform="translate(56 236)">
      <circle r="14" fill="#c0392b" fill-opacity=".14" class="buoy-pulse" />
      <circle r="6" fill="#c0392b" />
    </g>
    <text x="72" y="260" fill="currentColor" font-family="Martian Mono, monospace" font-size="10" fill-opacity=".75">31°14′N 121°29′E</text>

    <!-- Destination buoy -->
    <g transform="translate(448 52)">
      <circle r="14" fill="#1e8449" fill-opacity=".16" class="buoy-pulse" style="animation-delay: 1.2s" />
      <circle r="6" fill="#1e8449" />
    </g>
    <text x="428" y="48" text-anchor="end" fill="currentColor" font-family="Martian Mono, monospace" font-size="10" fill-opacity=".75">53°33′N 9°59′E</text>
  </svg>
</template>

<style scoped>
.vessel {
  offset-rotate: auto;
  animation: sail 7s cubic-bezier(0.45, 0, 0.25, 1) 2.4s infinite;
  offset-distance: 0%;
}
@keyframes sail {
  0% { offset-distance: 0%; opacity: 0; }
  8% { opacity: 1; }
  92% { opacity: 1; }
  100% { offset-distance: 100%; opacity: 0; }
}
.buoy-pulse {
  transform-box: fill-box;
  transform-origin: center;
  animation: pulse 2.6s ease-out infinite;
}
@keyframes pulse {
  from { transform: scale(0.6); opacity: 1; }
  to { transform: scale(2); opacity: 0; }
}
</style>
