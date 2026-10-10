<script setup lang="ts">
import type { Quote } from '~/types/sokan'

/** One forwarder's offer, as the customer sees it when comparing. */
const props = defineProps<{ q: Quote; best?: boolean; fastest?: boolean; canAct?: boolean; busy?: boolean }>()
defineEmits<{ accept: []; reject: [] }>()
const fmt = useFormat()
const open = ref(false)

const transit = computed(() => {
  const { transit_days_min: a, transit_days_max: b } = props.q
  if (a && b && a !== b) return `${fmt.number(a)}–${fmt.number(b)}`
  return a || b ? fmt.number(a || b) : '—'
})
const groups = computed(() => {
  const out: Record<string, number> = {}
  for (const c of props.q.charges) out[c.group] = (out[c.group] || 0) + c.amount
  return out
})
</script>

<template>
  <article
    class="relative overflow-hidden rounded-2xl border bg-surface transition-all duration-300"
    :class="[
      q.status === 'Accepted' ? 'border-success ring-4 ring-success/15' : best ? 'border-sea/50' : 'border-line',
      ['Rejected', 'Expired'].includes(q.status) && 'opacity-60',
    ]"
  >
    <div v-if="best || fastest || q.status === 'Accepted'" class="flex gap-2 px-5 pt-4">
      <span v-if="q.status === 'Accepted'" class="rounded-full bg-success px-2.5 py-1 text-xs font-bold text-white">{{ $t('quotes.booked') }}</span>
      <span v-if="best" class="rounded-full bg-night-900 px-2.5 py-1 text-xs font-bold text-white">{{ $t('quotes.bestPrice') }}</span>
      <span v-if="fastest" class="rounded-full bg-tide/15 px-2.5 py-1 text-xs font-bold text-sea dark:text-tide">{{ $t('quotes.fastest') }}</span>
    </div>
    <div class="grid gap-5 p-5 sm:grid-cols-[1fr_auto] sm:items-center">
      <div class="flex items-center gap-3">
        <CompanyAvatar v-if="q.forwarder" :name="q.forwarder.company_name" :logo="q.forwarder.logo" />
        <div class="min-w-0">
          <NuxtLinkLocale v-if="q.forwarder" :to="`/forwarders/${q.forwarder.slug}`" target="_blank" class="flex items-center gap-1 font-bold hover:text-sea">
            <span class="truncate">{{ q.forwarder.company_name }}</span>
            <AppIcon v-if="q.forwarder.is_verified" name="badge-check" :size="16" class="shrink-0 text-sea" />
          </NuxtLinkLocale>
          <p class="mt-0.5 flex flex-wrap items-center gap-x-3 text-xs text-muted">
            <span v-if="q.forwarder?.review_count" class="inline-flex items-center gap-1"><AppIcon name="star" :size="12" class="fill-warning text-warning" /> {{ fmt.number(q.forwarder.rating, 1) }}</span>
            <span>{{ fmt.flag(q.forwarder?.country_code) }} {{ q.forwarder?.country }}</span>
          </p>
        </div>
      </div>
      <div class="text-start sm:text-end">
        <p class="font-display text-4xl tabular-nums">{{ fmt.money(q.total_amount, q.currency) }}</p>
        <p class="text-xs text-muted">{{ $t('quotes.allIn') }}</p>
      </div>
    </div>

    <dl class="grid grid-cols-3 gap-px border-y border-line bg-line text-center text-sm">
      <div class="bg-surface p-3"><dt class="text-xs text-faint">{{ $t('quotes.transit') }}</dt><dd class="mt-0.5 font-bold">{{ transit }} {{ $t('units.days') }}</dd></div>
      <div class="bg-surface p-3"><dt class="text-xs text-faint">{{ $t('quotes.validUntil') }}</dt><dd class="mt-0.5 font-bold">{{ fmt.date(q.valid_until, 'short') }}</dd></div>
      <div class="bg-surface p-3"><dt class="text-xs text-faint">{{ $t('quotes.freeDays') }}</dt><dd class="mt-0.5 font-bold">{{ q.free_days != null ? fmt.number(q.free_days) : '—' }}</dd></div>
    </dl>

    <div class="p-5">
      <button type="button" class="flex w-full items-center justify-between text-sm font-semibold text-ink-soft" :aria-expanded="open" @click="open = !open">
        {{ $t('quotes.breakdown') }}
        <AppIcon name="chevron-down" :size="18" class="transition-transform" :class="open && 'rotate-180'" />
      </button>
      <div class="grid transition-[grid-template-rows] duration-400" :class="open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'">
        <div class="overflow-hidden">
          <div class="mt-4 space-y-2 text-sm">
            <div v-for="(c, i) in q.charges" :key="i" class="flex justify-between gap-4">
              <span class="text-muted">{{ c.description }} <span class="text-xs text-faint">· {{ fmt.label('chargeGroups', c.group) }}</span></span>
              <span class="font-semibold tabular-nums">{{ fmt.money(c.amount, q.currency) }}</span>
            </div>
          </div>
          <div class="mt-4 flex flex-wrap gap-2">
            <span v-for="(v, g) in groups" :key="g" class="rounded-lg bg-sunken px-2 py-1 text-xs">{{ fmt.label('chargeGroups', String(g)) }}: {{ fmt.money(v, q.currency) }}</span>
          </div>
          <div v-if="q.carrier || q.routing" class="mt-4 text-sm text-muted">
            <span v-if="q.carrier">{{ $t('quotes.carrier') }}: <b class="text-ink">{{ q.carrier }}</b></span>
            <span v-if="q.routing" class="ms-3">{{ $t('quotes.routing') }}: <b class="text-ink">{{ q.routing }}</b></span>
          </div>
          <p v-if="q.inclusions" class="mt-3 text-sm"><b>{{ $t('quotes.included') }}:</b> <span class="text-muted">{{ q.inclusions }}</span></p>
          <p v-if="q.exclusions" class="mt-1 text-sm"><b>{{ $t('quotes.excluded') }}:</b> <span class="text-muted">{{ q.exclusions }}</span></p>
          <p v-if="q.notes" class="mt-3 rounded-xl bg-sunken p-3 text-sm text-ink-soft">{{ q.notes }}</p>
        </div>
      </div>

      <div v-if="q.status === 'Accepted' && q.forwarder?.contact" class="mt-5 rounded-xl bg-success/10 p-4 text-sm">
        <p class="font-bold text-success">{{ $t('quotes.contactNow') }}</p>
        <p class="mt-2 flex flex-wrap gap-x-4 gap-y-1">
          <a :href="`mailto:${q.forwarder.contact.email}`" class="inline-flex items-center gap-1 font-semibold" dir="ltr"><AppIcon name="mail" :size="14" /> {{ q.forwarder.contact.email }}</a>
          <a v-if="q.forwarder.contact.phone" :href="`tel:${q.forwarder.contact.phone}`" class="inline-flex items-center gap-1 font-semibold" dir="ltr"><AppIcon name="phone" :size="14" /> {{ q.forwarder.contact.phone }}</a>
        </p>
      </div>

      <div v-if="canAct && q.status === 'Submitted'" class="mt-5 flex gap-2">
        <AppButton variant="primary" class="flex-1" icon="check" :loading="busy" @click="$emit('accept')">{{ $t('quotes.accept') }}</AppButton>
        <AppButton variant="ghost" :disabled="busy" @click="$emit('reject')">{{ $t('quotes.decline') }}</AppButton>
      </div>
      <p v-else-if="q.status !== 'Submitted' && q.status !== 'Accepted'" class="mt-4"><StatusPill :status="q.status" /></p>
    </div>
  </article>
</template>
