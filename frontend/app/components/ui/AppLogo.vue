<script setup lang="ts">
/**
 * The Sokan mark: a ship's helm (سکان means helm) drawn in chart ink, with
 * a buoy-red hub. The wordmark follows the visitor's language.
 */
withDefaults(defineProps<{ light?: boolean; compact?: boolean }>(), { light: false, compact: false })
const { locale } = useI18n()
</script>

<template>
  <span class="inline-flex items-center gap-2.5" :class="light ? 'text-white' : 'text-ink'">
    <svg viewBox="0 0 40 40" class="size-9 shrink-0" fill="none" aria-hidden="true">
      <circle cx="20" cy="20" r="11" stroke="currentColor" stroke-width="2.2" />
      <circle cx="20" cy="20" r="15.5" stroke="currentColor" stroke-width="1" stroke-dasharray="1.5 3" opacity=".55" />
      <g stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
        <path d="M20 2.5v8M20 29.5v8M2.5 20h8M29.5 20h8M7.6 7.6l5.7 5.7M26.7 26.7l5.7 5.7M32.4 7.6l-5.7 5.7M13.3 26.7l-5.7 5.7" />
      </g>
      <circle cx="20" cy="20" r="3.6" class="fill-buoy" :class="light && '!fill-[#ef6b5b]'" />
    </svg>
    <span v-if="!compact" class="font-display text-[1.6rem] leading-none">{{ locale === 'fa' ? 'سکان' : 'Sokan' }}</span>
  </span>
</template>
