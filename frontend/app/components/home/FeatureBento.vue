<script setup lang="ts">
/** Why Sokan: one large chart-plate tile comparing quotes, supporting notes around it. */
const notes = [
  { icon: 'shield-check', key: 'verified', tone: 'text-starboard' },
  { icon: 'lock', key: 'private', tone: 'text-buoy' },
  { icon: 'zap', key: 'fast', tone: 'text-sea' },
  { icon: 'star', key: 'reviews', tone: 'text-warning' },
]
const bars = [
  { w: 78, price: '$2,860' },
  { w: 64, price: '$2,640', best: true },
  { w: 92, price: '$2,915' },
]
</script>

<template>
  <section class="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
    <SectionHeading :eyebrow="$t('home.features.eyebrow')" :title="$t('home.features.title')" :subtitle="$t('home.features.subtitle')" />

    <div class="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div v-reveal class="card relative overflow-hidden p-7 sm:col-span-2 sm:p-9 lg:row-span-2">
        <ChartBackground :density="8" />
        <div class="relative">
          <p class="chart-label text-sea">{{ $t('home.features.compare.label') }}</p>
          <h3 class="font-display mt-3 text-3xl text-ink">{{ $t('home.features.compare.title') }}</h3>
          <p class="mt-3 max-w-md text-muted">{{ $t('home.features.compare.text') }}</p>
          <div class="mt-8 space-y-4">
            <div v-for="(b, i) in bars" :key="i" class="grid grid-cols-[5.5rem_1fr_auto] items-center gap-3">
              <span class="chart-label text-faint">{{ $t('home.features.compare.quote', { n: i + 1 }) }}</span>
              <div class="h-2.5 overflow-hidden rounded-full bg-sunken">
                <div v-reveal="200 + i * 150" class="h-full rounded-full" :class="b.best ? 'bg-starboard' : 'bg-line-strong'" :style="{ width: `${b.w}%` }" />
              </div>
              <span class="font-mono text-sm tabular-nums" :class="b.best ? 'text-starboard' : 'text-muted'">{{ b.price }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Grid flow: big tile fills 2×2, two notes stack beside it, the last row holds two notes + the free tile. -->
      <div v-for="(n, i) in notes" :key="n.key" v-reveal="80 + (i % 2) * 60" class="card p-6">
        <AppIcon :name="n.icon" :size="24" :class="n.tone" />
        <h3 class="mt-4 text-lg font-semibold">{{ $t(`home.features.${n.key}.title`) }}</h3>
        <p class="mt-1.5 text-sm text-muted">{{ $t(`home.features.${n.key}.text`) }}</p>
      </div>
      <div v-reveal="120" class="relative overflow-hidden rounded-2xl bg-night-900 p-6 text-white sm:col-span-2 lg:col-span-1">
        <ChartBackground tone="night" :density="6" />
        <div class="relative">
          <AppIcon name="coins" :size="24" class="text-tide" />
          <h3 class="mt-4 text-lg font-semibold">{{ $t('home.features.free.title') }}</h3>
          <p class="mt-1.5 text-sm text-white/70">{{ $t('home.features.free.text') }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
