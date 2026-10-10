<script setup lang="ts">
/** Night-chart band pitching the supply side, over a container terminal at night. */
const band = ref<HTMLElement | null>(null)
useParallax(band, 50)
const points = [
  { k: 'p1', icon: 'inbox' },
  { k: 'p2', icon: 'target' },
  { k: 'p3', icon: 'wallet' },
  { k: 'p4', icon: 'award' },
]
</script>

<template>
  <section class="px-4 py-8 sm:px-6 lg:px-8">
    <div ref="band" class="relative mx-auto max-w-7xl overflow-hidden rounded-3xl bg-night-950 px-6 py-14 text-white sm:px-12 lg:py-20">
      <div class="absolute inset-0" aria-hidden="true">
        <ChartPhoto name="night" alt="" sizes="(min-width: 1280px) 1280px, 100vw" class="parallax-layer size-full opacity-45" />
        <div class="absolute inset-0 bg-gradient-to-r from-night-950 via-night-950/80 to-night-950/30 rtl:bg-gradient-to-l" />
      </div>
      <ChartBackground tone="night" compass />
      <div class="relative grid items-center gap-12 lg:grid-cols-2">
        <div>
          <SectionHeading light align="start" :eyebrow="$t('home.forwarders.eyebrow')" :title="$t('home.forwarders.title')" :subtitle="$t('home.forwarders.subtitle')" />
          <div class="mt-8 flex flex-wrap gap-3">
            <AppButton to="/register/forwarder" variant="accent" size="lg" icon-end="arrow-right">{{ $t('home.forwarders.cta') }}</AppButton>
            <AppButton to="/for-forwarders" variant="night" size="lg">{{ $t('common.learnMore') }}</AppButton>
          </div>
        </div>
        <ul class="grid gap-3 sm:grid-cols-2">
          <li v-for="(p, i) in points" :key="p.k" v-reveal="i * 90" class="glass-night rounded-2xl p-5">
            <AppIcon :name="p.icon" :size="22" class="text-tide" />
            <h3 class="mt-3 font-semibold">{{ $t(`home.forwarders.${p.k}.title`) }}</h3>
            <p class="mt-1 text-sm text-white/65">{{ $t(`home.forwarders.${p.k}.text`) }}</p>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>
