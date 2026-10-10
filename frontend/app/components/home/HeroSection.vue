<script setup lang="ts">
import type { TransportMode } from '~/types/sokan'

/** Hero with an inline quick-start: pick a mode and lane, land in the wizard pre-filled. */
const props = defineProps<{ modes: TransportMode[] }>()
const { t } = useI18n()
const localePath = useLocalePath()

const mode = ref('')
const from = ref<string | null>(null)
const to = ref<string | null>(null)

watchEffect(() => {
  if (!mode.value && props.modes.length) mode.value = props.modes[0]!.name
})

function start() {
  navigateTo({
    path: localePath('/get-quote'),
    query: { mode: mode.value || undefined, from: from.value || undefined, to: to.value || undefined },
  })
}
</script>

<template>
  <!-- Clip only sideways: the country list must be free to drop below the hero. -->
  <section class="relative z-10 overflow-x-clip pt-[72px]">
    <ChartBackground compass />
    <div class="relative mx-auto grid max-w-7xl items-center gap-12 px-4 pt-10 pb-16 sm:px-6 lg:grid-cols-[1.05fr_1fr] lg:gap-14 lg:px-8 lg:pt-16 lg:pb-24">
      <div class="min-w-0">
        <p class="rise chart-label inline-flex items-center gap-2 text-sea">
          <span class="size-2 rounded-full bg-buoy" /> {{ t('home.hero.eyebrow') }}
        </p>

        <h1 class="rise font-display mt-5 text-[2.75rem] leading-[1.02] text-ink sm:text-6xl lg:text-[4.4rem]" style="--d: 60ms">
          {{ t('home.hero.title1') }}
          <span class="chart-em block">{{ t('home.hero.titleHighlight') }}</span>
        </h1>

        <p class="rise mt-6 max-w-xl text-lg leading-relaxed text-muted" style="--d: 140ms">
          {{ t('home.hero.subtitle') }}
        </p>

        <!-- Quick start -->
        <form class="rise card relative z-20 mt-8 max-w-xl p-3 sm:p-4" style="--d: 220ms" @submit.prevent="start">
          <div class="no-scrollbar -mx-1 flex gap-1.5 overflow-x-auto px-1 pb-3" role="radiogroup" :aria-label="t('wizard.route.title')">
            <button
              v-for="m in modes"
              :key="m.name"
              type="button"
              role="radio"
              :aria-checked="mode === m.name"
              class="inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors"
              :class="mode === m.name ? 'border-helm bg-helm text-helm-ink' : 'border-line-strong text-ink-soft hover:border-sea hover:text-sea'"
              @click="mode = m.name"
            >
              <AppIcon :name="m.icon" :size="15" />
              {{ $t(`modes.${m.code}.name`) }}
            </button>
          </div>
          <div class="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
            <CountrySelect v-model="from" :placeholder="t('home.hero.from')" />
            <CountrySelect v-model="to" :placeholder="t('home.hero.to')" />
            <AppButton type="submit" variant="accent" size="lg" icon-end="arrow-right" class="h-12">{{ t('home.hero.cta') }}</AppButton>
          </div>
        </form>

        <ul class="rise mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-soft" style="--d: 320ms">
          <li v-for="k in ['trust1', 'trust2', 'trust3']" :key="k" class="flex items-center gap-2">
            <AppIcon name="circle-check" :size="17" class="text-starboard" />
            {{ t(`home.hero.${k}`) }}
          </li>
        </ul>
      </div>

      <div class="rise relative min-w-0" style="--d: 180ms">
        <!-- Real freight behind the chart: a terminal from above and a ship under way, pinned like prints on a chart table. -->
        <div class="pointer-events-none absolute -top-10 -end-4 hidden w-[58%] sm:block lg:-top-14 lg:-end-10" aria-hidden="true">
          <div class="animate-float rotate-[4deg] overflow-hidden rounded-3xl border-4 border-surface shadow-2xl" style="animation-duration: 9s">
            <ChartPhoto name="port" alt="" sizes="(min-width: 1024px) 340px, 50vw" class="aspect-[4/3]" img-class="drift" />
          </div>
        </div>
        <div class="pointer-events-none absolute -bottom-10 -start-6 hidden w-[42%] lg:block" aria-hidden="true">
          <div class="animate-float -rotate-[5deg] overflow-hidden rounded-2xl border-4 border-surface shadow-xl" style="animation-duration: 11s; animation-delay: -4s">
            <ChartPhoto name="ship" alt="" sizes="240px" class="aspect-[4/3]" />
          </div>
        </div>
        <div class="relative">
          <HeroVisual />
        </div>
      </div>
    </div>
  </section>
</template>
