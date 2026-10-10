<script setup lang="ts">
/**
 * Responsive self-hosted photo: AVIF with a WebP fallback, real width and
 * height (no layout shift), lazy by default, and the photo's average tone
 * as the placeholder. `priority` is for the one image above the fold.
 */
import { PHOTOS, PHOTO_WIDTHS, type PhotoKey } from '~/utils/photos'

const props = withDefaults(
  defineProps<{
    name: PhotoKey
    alt: string
    sizes?: string
    priority?: boolean
    imgClass?: string
  }>(),
  { sizes: '(min-width: 1024px) 50vw, 100vw', priority: false },
)

const meta = computed(() => PHOTOS[props.name])
const widths = computed(() => PHOTO_WIDTHS.filter((w) => w <= ('maxWidth' in meta.value ? meta.value.maxWidth : 2200)))
const set = (ext: string) => widths.value.map((w) => `/photos/${props.name}-${w}.${ext} ${w}w`).join(', ')
</script>

<template>
  <picture class="block overflow-hidden" :style="{ backgroundColor: meta.color }">
    <source type="image/avif" :srcset="set('avif')" :sizes="sizes" />
    <source type="image/webp" :srcset="set('webp')" :sizes="sizes" />
    <img
      :src="`/photos/${name}-960.webp`"
      :alt="alt"
      :width="meta.w"
      :height="meta.h"
      :loading="priority ? 'eager' : 'lazy'"
      :fetchpriority="priority ? 'high' : 'auto'"
      decoding="async"
      class="size-full object-cover"
      :class="imgClass"
    />
  </picture>
</template>
