<script setup lang="ts">
/** Two audiences, one route: each step is a waypoint on a plotted line. */
const props = defineProps<{ initial?: 'shippers' | 'forwarders' }>()
const tab = ref<'shippers' | 'forwarders'>(props.initial ?? 'shippers')

const steps = {
  shippers: [
    { icon: 'send', key: 's1' },
    { icon: 'bell', key: 's2' },
    { icon: 'scale', key: 's3' },
    { icon: 'handshake', key: 's4' },
  ],
  forwarders: [
    { icon: 'inbox', key: 'f1' },
    { icon: 'lock-open', key: 'f2' },
    { icon: 'receipt', key: 'f3' },
    { icon: 'trending-up', key: 'f4' },
  ],
}
</script>

<template>
  <section id="how" class="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
    <SectionHeading :eyebrow="$t('home.how.eyebrow')" :title="$t('home.how.title')" :subtitle="$t('home.how.subtitle')" />

    <div class="mt-10 flex justify-center">
      <div class="relative inline-grid grid-cols-2 rounded-full border border-line-strong bg-surface p-1" role="tablist">
        <span
          class="absolute inset-y-1 w-[calc(50%-4px)] rounded-full bg-helm transition-all duration-500 ease-[var(--ease-spring)]"
          :class="tab === 'shippers' ? 'start-1' : 'start-1/2'"
        />
        <button
          v-for="k in (['shippers', 'forwarders'] as const)"
          :key="k"
          type="button"
          role="tab"
          :aria-selected="tab === k"
          class="relative z-10 px-5 py-2 text-sm font-semibold transition-colors sm:px-8"
          :class="tab === k ? 'text-helm-ink' : 'text-muted'"
          @click="tab = k"
        >
          {{ $t(`home.how.tab.${k}`) }}
        </button>
      </div>
    </div>

    <div class="relative mt-14">
      <!-- The route the waypoints sit on (desktop: horizontal, phone: vertical) -->
      <div class="absolute inset-x-[12%] top-6 hidden border-t-2 border-dashed border-sea/35 lg:block" />
      <div class="absolute inset-y-6 start-6 border-s-2 border-dashed border-sea/35 lg:hidden" />
      <Transition mode="out-in" enter-active-class="transition duration-500 ease-[var(--ease-spring)]" enter-from-class="opacity-0 translate-y-3" leave-active-class="transition duration-200" leave-to-class="opacity-0">
        <ol :key="tab" class="grid gap-8 lg:grid-cols-4 lg:gap-6">
          <li v-for="(s, i) in steps[tab]" :key="s.key" class="relative flex gap-5 lg:flex-col lg:items-center lg:text-center">
            <span class="relative grid size-12 shrink-0 place-items-center rounded-full border-2 border-sea bg-bg text-sea">
              <AppIcon :name="s.icon" :size="20" />
              <span class="absolute -top-1 -end-1 grid size-5 place-items-center rounded-full bg-buoy font-mono text-[10px] text-white">{{ i + 1 }}</span>
            </span>
            <div>
              <h3 class="text-lg font-semibold lg:mt-4">{{ $t(`home.how.${s.key}.title`) }}</h3>
              <p class="mt-1.5 max-w-xs text-sm leading-relaxed text-muted lg:mx-auto">{{ $t(`home.how.${s.key}.text`) }}</p>
            </div>
          </li>
        </ol>
      </Transition>
    </div>

    <div class="mt-12 flex justify-center">
      <AppButton v-if="tab === 'shippers'" to="/get-quote" variant="primary" size="lg" icon-end="arrow-right">{{ $t('home.how.ctaShipper') }}</AppButton>
      <AppButton v-else to="/register/forwarder" variant="primary" size="lg" icon-end="arrow-right">{{ $t('home.how.ctaForwarder') }}</AppButton>
    </div>
  </section>
</template>
