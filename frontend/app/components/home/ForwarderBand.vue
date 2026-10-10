<script setup lang="ts">
/** Dark band pitching the supply side. */
</script>

<template>
  <section class="px-4 py-8 sm:px-6 lg:px-8">
    <div class="relative mx-auto max-w-7xl overflow-hidden rounded-[2rem] bg-night-950 px-6 py-16 text-white sm:px-12 lg:py-20">
      <AuroraBackground />
      <div class="relative grid items-center gap-12 lg:grid-cols-2">
        <div>
          <SectionHeading light align="start" :eyebrow="$t('home.forwarders.eyebrow')" :title="$t('home.forwarders.title')" :subtitle="$t('home.forwarders.subtitle')" />
          <div class="mt-8 flex flex-wrap gap-3">
            <AppButton to="/register/forwarder" variant="accent" size="lg" icon-end="arrow-right">{{ $t('home.forwarders.cta') }}</AppButton>
            <AppButton to="/for-forwarders" variant="glass" size="lg">{{ $t('common.learnMore') }}</AppButton>
          </div>
        </div>
        <ul class="grid gap-3 sm:grid-cols-2">
          <li v-for="(k, i) in ['p1', 'p2', 'p3', 'p4']" :key="k" v-reveal="i * 90" class="glass-dark rounded-2xl p-5">
            <AppIcon :name="['inbox', 'target', 'wallet', 'award'][i]!" :size="24" class="text-lagoon" />
            <h3 class="mt-3 font-bold">{{ $t(`home.forwarders.${k}.title`) }}</h3>
            <p class="mt-1 text-sm text-white/60">{{ $t(`home.forwarders.${k}.text`) }}</p>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>
