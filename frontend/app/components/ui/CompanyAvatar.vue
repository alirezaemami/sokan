<script setup lang="ts">
/** Company logo, or a chart-style monogram (serif initials, tinted ring) when there is none. */
const props = withDefaults(defineProps<{ name: string; logo?: string | null; size?: 'sm' | 'md' | 'lg' | 'xl' }>(), { size: 'md' })
const sizes = { sm: 'size-9 text-sm', md: 'size-12 text-lg', lg: 'size-16 text-2xl', xl: 'size-24 text-4xl' }
const initials = computed(() =>
  props.name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase(),
)
// A stable hue per company, used only for the ring so it reads in both themes.
const hue = computed(() => [...props.name].reduce((a, c) => a + c.charCodeAt(0), 0) % 360)
</script>

<template>
  <span
    class="relative inline-grid shrink-0 place-items-center overflow-hidden rounded-full bg-sunken text-ink-soft"
    :class="sizes[size]"
    :style="{ boxShadow: `inset 0 0 0 2px hsl(${hue} 45% 50% / 0.45)` }"
  >
    <img v-if="logo" :src="logo" :alt="name" class="size-full bg-white object-contain p-1.5" loading="lazy" />
    <span v-else class="font-display leading-none">{{ initials }}</span>
  </span>
</template>
