<script setup lang="ts">
import type { TransportMode } from '~/types/sokan'

/**
 * The one job of a hero: mode, from, to → the request form, pre-filled.
 * `row` lays it out like a flight search; `stack` suits a side card, where
 * `tiles` shows the modes as tappable icons instead of a dropdown.
 */
const props = withDefaults(
  defineProps<{ modes: TransportMode[]; layout?: 'row' | 'stack'; modeStyle?: 'select' | 'tiles' }>(),
  { layout: 'row', modeStyle: 'select' },
)
const { t } = useI18n()
const localePath = useLocalePath()

const mode = ref('')
const from = ref<string | null>(null)
const to = ref<string | null>(null)

function start() {
  navigateTo({
    path: localePath('/get-quote'),
    query: { mode: mode.value || undefined, from: from.value || undefined, to: to.value || undefined },
  })
}
</script>

<template>
  <form :class="layout === 'row' ? 'grid gap-2 lg:grid-cols-[1.15fr_1fr_1fr_auto]' : 'grid gap-3'" @submit.prevent="start">
    <div v-if="modeStyle === 'tiles'" class="grid grid-cols-4 gap-2" role="radiogroup" :aria-label="t('home.hero.modeLabel')">
      <button
        v-for="m in props.modes"
        :key="m.name"
        type="button"
        role="radio"
        :aria-checked="mode === m.name"
        class="flex flex-col items-center gap-1.5 rounded-xl border px-1 py-2.5 text-center text-[11px] leading-tight font-semibold transition-colors sm:text-xs"
        :class="mode === m.name ? 'border-helm bg-helm text-helm-ink' : 'border-line-strong text-ink-soft hover:border-sea hover:text-sea'"
        @click="mode = mode === m.name ? '' : m.name"
      >
        <AppIcon :name="m.icon" :size="18" />
        <span class="line-clamp-2">{{ $t(`modes.${m.code}.name`) }}</span>
      </button>
    </div>
    <label v-else class="relative block">
      <span class="sr-only">{{ t('home.hero.modeLabel') }}</span>
      <AppIcon name="layers" :size="18" class="pointer-events-none absolute start-4 top-1/2 -translate-y-1/2 text-faint" />
      <select
        v-model="mode"
        class="h-12 w-full appearance-none rounded-xl border border-line-strong bg-surface ps-11 pe-10 text-ink outline-none focus:border-sea focus:ring-4 focus:ring-[var(--ring)]"
      >
        <option value="">{{ t('home.hero.anyMode') }}</option>
        <option v-for="m in props.modes" :key="m.name" :value="m.name">{{ $t(`modes.${m.code}.name`) }}</option>
      </select>
      <AppIcon name="chevron-down" :size="18" class="pointer-events-none absolute end-4 top-1/2 -translate-y-1/2 text-faint" />
    </label>

    <div :class="layout === 'row' ? 'contents' : 'grid gap-3 sm:grid-cols-2'">
      <CountrySelect v-model="from" :placeholder="t('home.hero.from')" />
      <CountrySelect v-model="to" :placeholder="t('home.hero.to')" />
    </div>
    <AppButton type="submit" variant="accent" size="lg" icon-end="arrow-right" class="h-12" :block="layout === 'stack'">{{ t('home.hero.cta') }}</AppButton>
  </form>
</template>
