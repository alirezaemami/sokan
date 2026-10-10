<script setup lang="ts">
import type { LeadItem } from '~/types/sokan'

defineProps<{ r: LeadItem }>()
const fmt = useFormat()
</script>

<template>
  <NuxtLinkLocale
    :to="`/partner/leads/${r.name}`"
    class="card group relative block overflow-hidden p-5 transition-all hover:-translate-y-0.5 hover:border-sea/40 hover:shadow-lg"
  >
    <span v-if="r.lead.is_new" class="absolute inset-y-0 start-0 w-1 bg-night-900" />
    <div class="flex items-center justify-between gap-3">
      <span class="flex items-center gap-2 text-xs font-semibold text-faint">
        <span v-if="r.lead.is_new" class="rounded-md bg-buoy px-1.5 py-0.5 text-[0.65rem] font-bold text-white uppercase">{{ $t('common.new') }}</span>
        {{ fmt.relative(r.lead.sent_on) }}
      </span>
      <StatusPill :status="r.lead.status" group="leadStatus" />
    </div>
    <RouteLine class="mt-4" :origin="r.origin" :destination="r.destination" :icon="r.mode?.icon" />
    <p class="mt-4 truncate text-sm font-semibold">{{ r.cargo.commodity }}</p>
    <CargoChips class="mt-2" :r="r" />
    <div class="mt-4 flex items-center justify-between gap-3 border-t border-line pt-4 text-xs text-muted">
      <span class="inline-flex items-center gap-1"><AppIcon name="calendar" :size="14" /> {{ $t('leads.ready') }} {{ fmt.date(r.ready_date, 'short') }}</span>
      <span class="inline-flex items-center gap-1"><AppIcon name="users" :size="14" /> {{ $t('leads.competition', { n: fmt.number(r.quote_count) }) }}</span>
    </div>
  </NuxtLinkLocale>
</template>
