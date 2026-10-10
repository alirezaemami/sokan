<script setup lang="ts">
import type { Place } from '~/types/sokan'

withDefaults(defineProps<{ origin: Place; destination: Place; icon?: string; size?: 'sm' | 'lg' }>(), { icon: 'ship', size: 'sm' })
const fmt = useFormat()
</script>

<template>
  <div class="flex items-center gap-3">
    <div class="min-w-0">
      <p class="truncate font-bold" :class="size === 'lg' ? 'text-xl sm:text-2xl' : ''">{{ fmt.flag(origin.country_code) }} {{ origin.city || fmt.country(origin.country_code, origin.country) }}</p>
      <p class="truncate text-xs text-muted">{{ origin.port || fmt.country(origin.country_code, origin.country) }}</p>
    </div>
    <div class="relative mx-1 flex min-w-10 flex-1 items-center">
      <span class="size-1.5 rounded-full bg-brand" />
      <span class="h-px flex-1 border-t-2 border-dashed border-brand/30" />
      <span class="grid size-7 place-items-center rounded-full bg-brand/10 text-brand"><AppIcon :name="icon" :size="14" /></span>
      <span class="h-px flex-1 border-t-2 border-dashed border-lagoon/40" />
      <span class="size-1.5 rounded-full bg-lagoon" />
    </div>
    <div class="min-w-0 text-end">
      <p class="truncate font-bold" :class="size === 'lg' ? 'text-xl sm:text-2xl' : ''">{{ fmt.flag(destination.country_code) }} {{ destination.city || fmt.country(destination.country_code, destination.country) }}</p>
      <p class="truncate text-xs text-muted">{{ destination.port || fmt.country(destination.country_code, destination.country) }}</p>
    </div>
  </div>
</template>
