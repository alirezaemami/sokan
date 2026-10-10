<script setup lang="ts">
/** Two audiences, one flow — tabs switch the story with an animated indicator. */
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
  <section id="how" class="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
    <SectionHeading :eyebrow="$t('home.how.eyebrow')" :title="$t('home.how.title')" :subtitle="$t('home.how.subtitle')" />

    <div class="mt-10 flex justify-center">
      <div class="relative inline-grid grid-cols-2 rounded-2xl bg-sunken p-1.5" role="tablist">
        <span
          class="absolute inset-y-1.5 w-[calc(50%-6px)] rounded-xl bg-surface shadow-md transition-all duration-500 ease-[var(--ease-spring)]"
          :class="tab === 'shippers' ? 'start-1.5' : 'start-1/2'"
        />
        <button
          v-for="k in (['shippers', 'forwarders'] as const)"
          :key="k"
          type="button"
          role="tab"
          :aria-selected="tab === k"
          class="relative z-10 px-5 py-2.5 text-sm font-bold transition-colors sm:px-8"
          :class="tab === k ? 'text-ink' : 'text-muted'"
          @click="tab = k"
        >
          {{ $t(`home.how.tab.${k}`) }}
        </button>
      </div>
    </div>

    <div class="relative mt-14">
      <div class="absolute inset-x-[12%] top-9 hidden h-px bg-gradient-to-r from-brand/0 via-brand/40 to-lagoon/0 lg:block" />
      <Transition mode="out-in" enter-active-class="transition duration-500 ease-[var(--ease-spring)]" enter-from-class="opacity-0 translate-y-4" leave-active-class="transition duration-200" leave-to-class="opacity-0">
        <ol :key="tab" class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <li v-for="(s, i) in steps[tab]" :key="s.key" class="relative text-center">
            <div class="relative mx-auto grid size-18 place-items-center rounded-3xl bg-surface shadow-lg ring-1 ring-line">
              <span class="absolute -top-2 -end-2 grid size-7 place-items-center rounded-full bg-brand-gradient text-xs font-bold text-white">{{ i + 1 }}</span>
              <AppIcon :name="s.icon" :size="28" class="text-brand" />
            </div>
            <h3 class="mt-6 text-lg font-bold">{{ $t(`home.how.${s.key}.title`) }}</h3>
            <p class="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-muted">{{ $t(`home.how.${s.key}.text`) }}</p>
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
