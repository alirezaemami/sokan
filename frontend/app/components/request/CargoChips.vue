<script setup lang="ts">
import type { RequestTeaser } from '~/types/sokan'

defineProps<{ r: RequestTeaser }>()
const fmt = useFormat()
</script>

<template>
  <div class="flex flex-wrap gap-1.5 text-xs">
    <span v-if="r.mode" class="inline-flex items-center gap-1 rounded-lg bg-sea/10 px-2 py-1 font-semibold text-sea">
      <AppIcon :name="r.mode.icon" :size="13" /> {{ $t(`modes.${r.mode.code}.name`) }}
    </span>
    <span v-for="c in r.cargo.containers" :key="c.type" class="rounded-lg bg-sunken px-2 py-1 font-medium">{{ fmt.number(c.qty) }} × {{ c.type }}</span>
    <span v-if="!r.cargo.containers.length && r.cargo.total_weight_kg" class="rounded-lg bg-sunken px-2 py-1 font-medium">{{ fmt.weight(r.cargo.total_weight_kg) }}</span>
    <span v-if="r.cargo.total_volume_cbm" class="rounded-lg bg-sunken px-2 py-1 font-medium">{{ fmt.number(r.cargo.total_volume_cbm, 2) }} {{ $t('units.cbm') }}</span>
    <span v-if="r.cargo.category !== 'General Cargo'" class="rounded-lg bg-warning/12 px-2 py-1 font-semibold text-warning">{{ fmt.label('categories', r.cargo.category) }}</span>
    <span v-if="r.incoterm" class="rounded-lg bg-sunken px-2 py-1 font-medium">{{ r.incoterm }}</span>
  </div>
</template>
