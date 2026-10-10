<script setup lang="ts">
import type { ForwarderCard } from '~/types/sokan'

defineProps<{ f: ForwarderCard }>()
const fmt = useFormat()
const { modes } = useModes()
const modeIcon = (name: string) => modes.value.find((m) => m.name === name)?.icon || 'package'
</script>

<template>
  <NuxtLinkLocale :to="`/forwarders/${f.slug}`" class="card group flex h-full flex-col p-5 transition-all duration-300 hover:-translate-y-1 hover:border-sea/40 hover:shadow-xl">
    <div class="flex items-start gap-4">
      <CompanyAvatar :name="f.company_name" :logo="f.logo" size="lg" />
      <div class="min-w-0 flex-1">
        <h3 class="flex items-center gap-1.5 font-bold">
          <span class="truncate">{{ f.company_name }}</span>
          <AppIcon v-if="f.is_verified" name="badge-check" :size="18" class="shrink-0 text-sea" :aria-label="$t('common.verified')" />
        </h3>
        <p class="mt-0.5 truncate text-sm text-muted">{{ fmt.flag(f.country_code) }} {{ fmt.place(f) }}</p>
        <div v-if="f.review_count" class="mt-1.5 flex items-center gap-1.5 text-sm">
          <RatingStars :model-value="f.rating" :size="14" />
          <span class="text-xs text-faint">({{ fmt.number(f.review_count) }})</span>
        </div>
      </div>
    </div>
    <p v-if="f.tagline" class="mt-4 line-clamp-2 text-sm text-ink-soft">{{ f.tagline }}</p>
    <figure v-if="f.review" class="relative mt-4 rounded-xl bg-sunken/70 p-4">
      <span class="font-display pointer-events-none absolute -top-3 start-3 text-4xl leading-none text-buoy/70" aria-hidden="true">“</span>
      <blockquote class="line-clamp-3 text-sm leading-relaxed text-ink-soft">{{ f.review.comment }}</blockquote>
      <figcaption class="mt-2 flex items-center gap-2 text-xs text-faint">
        <RatingStars :model-value="f.review.rating" :size="12" />
        <span class="truncate">{{ f.review.author }} · {{ fmt.relative(f.review.creation) }}</span>
      </figcaption>
    </figure>
    <div class="mt-auto flex items-center justify-between gap-3 pt-5">
      <div class="flex -space-x-1.5 rtl:space-x-reverse">
        <span v-for="m in (f.modes || []).slice(0, 5)" :key="m" class="grid size-8 place-items-center rounded-full bg-sunken text-ink-soft ring-2 ring-surface" :title="m">
          <AppIcon :name="modeIcon(m)" :size="15" />
        </span>
      </div>
      <span class="inline-flex items-center gap-1 text-sm font-semibold text-sea opacity-0 transition-opacity group-hover:opacity-100">
        {{ $t('common.view') }} <AppIcon name="arrow-right" :size="14" flip />
      </span>
    </div>
  </NuxtLinkLocale>
</template>
