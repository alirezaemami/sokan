<script setup lang="ts">
import type { TransportMode } from '~/types/sokan'

/** Hero with an inline quick-start: pick a mode and lane, land in the wizard pre-filled. */
const props = defineProps<{ modes: TransportMode[] }>()
const { t } = useI18n()
const localePath = useLocalePath()

const mode = ref<string>('')
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
  <section class="relative overflow-hidden bg-night-950 pt-[72px] text-white">
    <AuroraBackground />
    <div class="relative mx-auto grid max-w-7xl items-center gap-14 px-4 pt-14 pb-20 sm:px-6 lg:grid-cols-[1.08fr_1fr] lg:gap-10 lg:px-8 lg:pt-20 lg:pb-28">
      <div>
        <p
          class="rise glass-dark inline-flex items-center gap-2 rounded-full py-1.5 ps-1.5 pe-4 text-sm text-white/80"
        >
          <span class="rounded-full bg-brand-gradient px-2.5 py-0.5 text-xs font-bold text-white">{{ t('home.hero.badge') }}</span>
          {{ t('home.hero.eyebrow') }}
        </p>

        <h1 style="--d: 80ms"
          class="rise mt-6 text-[2.6rem] leading-[1.05] font-extrabold tracking-tight sm:text-6xl lg:text-[4.2rem]"
        >
          {{ t('home.hero.title1') }}
          <span class="text-gradient block">{{ t('home.hero.titleHighlight') }}</span>
        </h1>

        <p style="--d: 160ms"
          class="rise mt-6 max-w-xl text-lg leading-relaxed text-white/70 sm:text-xl"
        >
          {{ t('home.hero.subtitle') }}
        </p>

        <!-- Quick start -->
        <form style="--d: 260ms"
          class="rise glass-dark mt-9 max-w-xl rounded-3xl p-3 shadow-2xl shadow-black/30 sm:p-4"
          @submit.prevent="start"
        >
          <div class="no-scrollbar -mx-1 flex gap-1.5 overflow-x-auto px-1 pb-3">
            <button
              v-for="m in modes"
              :key="m.name"
              type="button"
              class="inline-flex shrink-0 items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold transition-all"
              :class="mode === m.name ? 'bg-white text-night-950 shadow-lg' : 'text-white/70 hover:bg-white/10 hover:text-white'"
              @click="mode = m.name"
            >
              <AppIcon :name="m.icon" :size="16" />
              {{ $t(`modes.${m.code}.name`) }}
            </button>
          </div>
          <div class="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
            <div class="hero-select"><CountrySelect v-model="from" :placeholder="t('home.hero.from')" /></div>
            <div class="hero-select"><CountrySelect v-model="to" :placeholder="t('home.hero.to')" /></div>
            <AppButton type="submit" variant="accent" size="lg" icon-end="arrow-right" class="h-12">{{ t('home.hero.cta') }}</AppButton>
          </div>
        </form>

        <ul style="--d: 450ms"
          class="rise mt-7 flex flex-wrap gap-x-6 gap-y-3 text-sm text-white/70"
        >
          <li v-for="k in ['trust1', 'trust2', 'trust3']" :key="k" class="flex items-center gap-2">
            <AppIcon name="circle-check" :size="18" class="text-lagoon" />
            {{ t(`home.hero.${k}`) }}
          </li>
        </ul>
      </div>

      <div style="--d: 200ms"
      >
        <HeroVisual />
      </div>
    </div>

    <!-- Curved bottom edge into the page -->
    <svg class="relative block w-full text-bg" viewBox="0 0 1440 60" preserveAspectRatio="none" aria-hidden="true">
      <path fill="currentColor" d="M0 60h1440V0c-240 40-480 60-720 60S240 40 0 0z" />
    </svg>
  </section>
</template>

<style scoped>
/* The country picker is a light-surface control; inside the dark hero it
   reads better as glass. */
.hero-select :deep(button) {
  background: rgb(255 255 255 / 0.08);
  border-color: rgb(255 255 255 / 0.12);
  color: #fff;
}
.hero-select :deep(button span) {
  color: rgb(255 255 255 / 0.85);
}
</style>
