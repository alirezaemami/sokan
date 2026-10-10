<script setup lang="ts">
import type { CustomerRequestRow } from '~/types/sokan'

defineProps<{ r: CustomerRequestRow }>()
const fmt = useFormat()
</script>

<template>
  <NuxtLinkLocale :to="`/account/requests/${r.name}`" class="card group block p-5 transition-all hover:-translate-y-0.5 hover:border-brand/40 hover:shadow-lg">
    <div class="flex items-center justify-between gap-3">
      <span class="text-xs font-semibold text-faint">{{ r.name }} · {{ fmt.relative(r.creation) }}</span>
      <StatusPill :status="r.status" />
    </div>
    <RouteLine class="mt-4" :origin="r.origin" :destination="r.destination" :icon="r.mode?.icon" />
    <CargoChips class="mt-4" :r="r" />
    <div class="mt-4 flex items-center justify-between gap-3 border-t border-line pt-4 text-sm">
      <span class="text-muted">
        <b class="text-ink">{{ fmt.number(r.quote_count) }}</b> {{ $t('requests.quotes', r.quote_count) }}
        <template v-if="r.status === 'Open'"> · {{ $t('requests.sentTo', { n: fmt.number(r.leads_sent) }) }}</template>
      </span>
      <span v-if="r.best_quote" class="font-bold text-success">{{ $t('requests.from') }} {{ fmt.money(r.best_quote.total_amount, r.best_quote.currency) }}</span>
      <AppIcon v-else name="arrow-right" :size="18" flip class="text-faint transition-transform group-hover:translate-x-1 rtl:group-hover:-translate-x-1" />
    </div>
  </NuxtLinkLocale>
</template>
