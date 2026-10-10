<script setup lang="ts">
/**
 * Stylised globe with trade lanes that draw themselves and cargo dots that
 * travel along them. Pure SVG + CSS offset-path: renders on the server, costs
 * nothing on the main thread, and freezes under prefers-reduced-motion.
 */
const lanes = [
  { d: 'M92 150 Q 200 40 318 132', delay: 0, color: '#22d3ee' },
  { d: 'M110 262 Q 210 170 300 250', delay: 1.2, color: '#a5b4fc' },
  { d: 'M150 96 Q 250 160 270 310', delay: 2.1, color: '#ff8a6e' },
  { d: 'M318 132 Q 300 230 200 318', delay: 0.6, color: '#22d3ee' },
  { d: 'M92 150 Q 120 250 200 318', delay: 1.7, color: '#a5b4fc' },
]
const ports = [
  [92, 150], [318, 132], [110, 262], [300, 250], [150, 96], [270, 310], [200, 318],
]
</script>

<template>
  <svg viewBox="0 0 400 400" fill="none" aria-hidden="true">
    <defs>
      <radialGradient id="globe-fill" cx="38%" cy="32%" r="75%">
        <stop offset="0" stop-color="#2a3170" />
        <stop offset=".55" stop-color="#121a3a" />
        <stop offset="1" stop-color="#070b1c" />
      </radialGradient>
      <radialGradient id="globe-glow" cx="50%" cy="50%" r="50%">
        <stop offset=".72" stop-color="#5b5cf6" stop-opacity="0" />
        <stop offset=".88" stop-color="#5b5cf6" stop-opacity=".35" />
        <stop offset="1" stop-color="#22d3ee" stop-opacity="0" />
      </radialGradient>
      <clipPath id="globe-clip"><circle cx="200" cy="200" r="150" /></clipPath>
    </defs>

    <circle cx="200" cy="200" r="196" fill="url(#globe-glow)" />
    <circle cx="200" cy="200" r="150" fill="url(#globe-fill)" stroke="rgb(255 255 255 / .12)" />

    <!-- Graticule, slowly rotating so the globe feels alive. -->
    <g clip-path="url(#globe-clip)" stroke="rgb(255 255 255 / .07)">
      <g class="globe-spin">
        <ellipse v-for="rx in [150, 115, 75, 30]" :key="rx" cx="200" cy="200" :rx="rx" ry="150" />
      </g>
      <ellipse v-for="(ry, i) in [140, 110, 70, 20]" :key="i" cx="200" :cy="200" rx="150" :ry="ry" transform="rotate(0)" />
      <line x1="50" y1="200" x2="350" y2="200" />
      <!-- Dotted land masses, abstract on purpose. -->
      <g fill="rgb(165 180 252 / .22)" stroke="none">
        <circle v-for="n in 90" :key="n" :cx="70 + ((n * 37) % 260)" :cy="80 + ((n * 53) % 240)" r="1.6" />
      </g>
    </g>

    <!-- Lanes -->
    <g stroke-linecap="round">
      <path v-for="(l, i) in lanes" :key="`p${i}`" :d="l.d" :stroke="l.color" stroke-opacity=".25" stroke-width="1.5" />
      <path
        v-for="(l, i) in lanes"
        :key="`a${i}`"
        :d="l.d"
        :stroke="l.color"
        stroke-width="1.8"
        stroke-dasharray="6 14"
        class="animate-dash"
        :style="{ animationDelay: `-${l.delay}s` }"
      />
    </g>

    <!-- Cargo travelling along each lane -->
    <circle
      v-for="(l, i) in lanes"
      :key="`c${i}`"
      r="4"
      :fill="l.color"
      class="cargo-dot"
      :style="{ offsetPath: `path('${l.d}')`, animationDelay: `${l.delay}s`, filter: `drop-shadow(0 0 6px ${l.color})` }"
    />

    <!-- Ports -->
    <g v-for="([x, y], i) in ports" :key="`port${i}`">
      <circle :cx="x" :cy="y" r="9" fill="#22d3ee" fill-opacity=".15" class="port-pulse" :style="{ animationDelay: `${i * 0.4}s`, transformOrigin: `${x}px ${y}px` }" />
      <circle :cx="x" :cy="y" r="3.5" fill="#fff" />
    </g>
  </svg>
</template>

<style scoped>
.cargo-dot {
  offset-distance: 0%;
  animation: travel 4.8s cubic-bezier(0.45, 0, 0.25, 1) infinite;
}
@keyframes travel {
  0% { offset-distance: 0%; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { offset-distance: 100%; opacity: 0; }
}
.port-pulse {
  animation: pulse 2.8s ease-out infinite;
}
@keyframes pulse {
  0% { transform: scale(0.6); opacity: 0.9; }
  100% { transform: scale(2.2); opacity: 0; }
}
.globe-spin {
  transform-origin: 200px 200px;
  animation: sway 18s ease-in-out infinite alternate;
}
@keyframes sway {
  from { transform: scaleX(1); }
  to { transform: scaleX(0.55); }
}
</style>
