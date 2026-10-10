<script setup lang="ts">
/** Company logo, or a gradient monogram when there is none. */
const props = withDefaults(defineProps<{ name: string; logo?: string | null; size?: 'sm' | 'md' | 'lg' | 'xl' }>(), { size: 'md' })
const sizes = { sm: 'size-9 text-xs rounded-lg', md: 'size-12 text-sm rounded-xl', lg: 'size-16 text-lg rounded-2xl', xl: 'size-24 text-2xl rounded-3xl' }
const initials = computed(() =>
  props.name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase(),
)
const hue = computed(() => [...props.name].reduce((a, c) => a + c.charCodeAt(0), 0) % 360)
</script>

<template>
  <span class="relative inline-grid shrink-0 place-items-center overflow-hidden font-bold text-white ring-1 ring-line" :class="sizes[size]">
    <img v-if="logo" :src="logo" :alt="name" class="size-full bg-white object-contain p-1" loading="lazy" />
    <span
      v-else
      class="grid size-full place-items-center"
      :style="{ background: `linear-gradient(135deg, hsl(${hue} 75% 58%), hsl(${(hue + 50) % 360} 80% 45%))` }"
    >{{ initials }}</span>
  </span>
</template>
