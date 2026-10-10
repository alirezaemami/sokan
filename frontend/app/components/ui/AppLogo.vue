<script setup lang="ts">
/** The Sokan mark: a ship's helm (سکان) whose spokes double as route lines. */
withDefaults(defineProps<{ light?: boolean; compact?: boolean }>(), { light: false, compact: false })
</script>

<template>
  <span class="inline-flex items-center gap-2.5" :class="light ? 'text-white' : 'text-ink'">
    <svg viewBox="0 0 40 40" class="size-9 shrink-0" aria-hidden="true">
      <defs>
        <linearGradient id="sokan-g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#5b5cf6" />
          <stop offset=".55" stop-color="#7c3aed" />
          <stop offset="1" stop-color="#22d3ee" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="12" fill="url(#sokan-g)" />
      <g fill="none" stroke="#fff" stroke-linecap="round" stroke-width="2.4">
        <circle cx="20" cy="20" r="7.5" />
        <path d="M20 6.5v6M20 27.5v6M6.5 20h6M27.5 20h6M10.4 10.4l4.3 4.3M25.3 25.3l4.3 4.3M29.6 10.4l-4.3 4.3M14.7 25.3l-4.3 4.3" />
      </g>
      <circle cx="20" cy="20" r="2.6" fill="#fff" />
    </svg>
    <span v-if="!compact" class="text-[1.35rem] font-extrabold tracking-tight">Sokan</span>
  </span>
</template>
