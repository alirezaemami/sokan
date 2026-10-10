<script setup lang="ts">
/** Why Sokan, as a bento grid: one hero tile, supporting tiles around it. */
</script>

<template>
  <section class="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
    <SectionHeading :eyebrow="$t('home.features.eyebrow')" :title="$t('home.features.title')" :subtitle="$t('home.features.subtitle')" />

    <div class="mt-14 grid gap-4 md:grid-cols-6">
      <!-- Compare -->
      <div v-reveal class="card relative overflow-hidden p-7 md:col-span-4 md:row-span-2 sm:p-9">
        <div class="absolute -end-24 -top-24 size-72 rounded-full bg-brand/15 blur-3xl" />
        <AppIcon name="scale" :size="28" class="text-brand" />
        <h3 class="mt-5 text-2xl font-extrabold">{{ $t('home.features.compare.title') }}</h3>
        <p class="mt-2 max-w-md text-muted">{{ $t('home.features.compare.text') }}</p>
        <div class="mt-8 space-y-3">
          <div v-for="(row, i) in [72, 58, 88]" :key="i" class="flex items-center gap-3">
            <span class="w-24 shrink-0 text-xs font-semibold text-faint">{{ $t('home.features.compare.quote', { n: i + 1 }) }}</span>
            <div class="h-3 flex-1 overflow-hidden rounded-full bg-sunken">
              <div
                v-reveal="200 + i * 150"
                class="h-full origin-left rounded-full rtl:origin-right"
                :class="i === 1 ? 'bg-brand-gradient' : 'bg-line-strong'"
                :style="{ width: `${row}%` }"
              />
            </div>
            <span v-if="i === 1" class="rounded-full bg-success/12 px-2 py-0.5 text-xs font-bold text-success">{{ $t('home.features.compare.best') }}</span>
          </div>
        </div>
      </div>

      <div v-reveal="80" class="card p-7 md:col-span-2">
        <AppIcon name="shield-check" :size="26" class="text-success" />
        <h3 class="mt-4 text-lg font-bold">{{ $t('home.features.verified.title') }}</h3>
        <p class="mt-1.5 text-sm text-muted">{{ $t('home.features.verified.text') }}</p>
      </div>
      <div v-reveal="160" class="card p-7 md:col-span-2">
        <AppIcon name="lock" :size="26" class="text-coral" />
        <h3 class="mt-4 text-lg font-bold">{{ $t('home.features.private.title') }}</h3>
        <p class="mt-1.5 text-sm text-muted">{{ $t('home.features.private.text') }}</p>
      </div>

      <div v-reveal class="card p-7 md:col-span-2">
        <AppIcon name="zap" :size="26" class="text-warning" />
        <h3 class="mt-4 text-lg font-bold">{{ $t('home.features.fast.title') }}</h3>
        <p class="mt-1.5 text-sm text-muted">{{ $t('home.features.fast.text') }}</p>
      </div>
      <div v-reveal="80" class="card p-7 md:col-span-2">
        <AppIcon name="star" :size="26" class="text-brand" />
        <h3 class="mt-4 text-lg font-bold">{{ $t('home.features.reviews.title') }}</h3>
        <p class="mt-1.5 text-sm text-muted">{{ $t('home.features.reviews.text') }}</p>
      </div>
      <div v-reveal="160" class="relative overflow-hidden rounded-2xl bg-brand-gradient p-7 text-white md:col-span-2">
        <AppIcon name="coins" :size="26" />
        <h3 class="mt-4 text-lg font-bold">{{ $t('home.features.free.title') }}</h3>
        <p class="mt-1.5 text-sm text-white/80">{{ $t('home.features.free.text') }}</p>
      </div>
    </div>
  </section>
</template>
