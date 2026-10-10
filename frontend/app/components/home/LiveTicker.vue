<script setup lang="ts">
import type { LiveRequest } from '~/types/sokan'

/**
 * Infinite marquee of real, recent requests (lanes and modes only — never
 * who or what). With too few requests to look alive, it shows popular trade
 * lanes instead, labelled as such, rather than inventing activity.
 */
const props = defineProps<{ live: LiveRequest[] }>()
const fmt = useFormat()

const POPULAR: [string, string, string][] = [
  ['CN', 'DE', 'ship'], ['TR', 'IQ', 'truck'], ['AE', 'IR', 'ship'], ['CN', 'US', 'plane'],
  ['IN', 'AE', 'ship'], ['DE', 'PL', 'truck'], ['CN', 'KZ', 'train-front'], ['NL', 'GB', 'truck'],
  ['VN', 'US', 'ship'], ['KR', 'RU', 'train-front'], ['IT', 'EG', 'ship'], ['US', 'MX', 'truck'],
]

const isLive = computed(() => props.live.length >= 6)
const items = computed(() =>
  isLive.value
    ? props.live.map((r) => ({ from: r.origin, to: r.destination, icon: r.mode?.icon || 'package', quotes: r.quote_count, when: r.published_on }))
    : POPULAR.map(([a, b, icon]) => ({
        from: { country_code: a, city: null, country: null },
        to: { country_code: b, city: null, country: null },
        icon,
        quotes: null as number | null,
        when: null as string | null,
      })),
)
</script>

<template>
  <section class="relative py-10" :aria-label="isLive ? $t('home.live.title') : $t('home.live.popular')">
    <div class="mx-auto mb-5 flex max-w-7xl items-center gap-3 px-4 sm:px-6 lg:px-8">
      <span class="relative flex size-2.5">
        <span v-if="isLive" class="animate-ping-slow absolute inline-flex size-full rounded-full bg-success" />
        <span class="relative size-2.5 rounded-full" :class="isLive ? 'bg-success' : 'bg-brand'" />
      </span>
      <p class="text-sm font-bold text-ink-soft">{{ isLive ? $t('home.live.title') : $t('home.live.popular') }}</p>
    </div>
    <div class="marquee-mask overflow-hidden">
      <div class="marquee-track animate-marquee flex w-max gap-4" style="--marquee-duration: 55s">
        <template v-for="copy in 2" :key="copy">
          <div
            v-for="(it, i) in items"
            :key="`${copy}-${i}`"
            class="card flex shrink-0 items-center gap-3 px-4 py-3"
            :aria-hidden="copy === 2 || undefined"
          >
            <span class="grid size-9 place-items-center rounded-xl bg-brand/10 text-brand"><AppIcon :name="it.icon" :size="18" /></span>
            <span class="text-sm font-semibold whitespace-nowrap">
              {{ fmt.flag(it.from.country_code) }} {{ it.from.city || fmt.country(it.from.country_code) }}
              <AppIcon name="arrow-right" :size="14" flip class="mx-1 inline text-faint" />
              {{ fmt.flag(it.to.country_code) }} {{ it.to.city || fmt.country(it.to.country_code) }}
            </span>
            <span v-if="it.quotes" class="rounded-full bg-success/12 px-2 py-0.5 text-xs font-bold text-success">
              {{ $t('home.live.quotes', { n: fmt.number(it.quotes) }) }}
            </span>
            <span v-else-if="it.when" class="text-xs text-faint">{{ fmt.relative(it.when) }}</span>
          </div>
        </template>
      </div>
    </div>
  </section>
</template>
