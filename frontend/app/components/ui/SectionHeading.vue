<script setup lang="ts">
withDefaults(
  defineProps<{ eyebrow?: string; title: string; subtitle?: string; align?: 'center' | 'start'; light?: boolean; as?: 'h1' | 'h2' }>(),
  { align: 'center', light: false, as: 'h2' },
)
</script>

<template>
  <div :class="align === 'center' ? 'mx-auto max-w-2xl text-center' : 'max-w-2xl'">
    <p
      v-if="eyebrow"
      v-reveal
      class="mb-4 inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-xs font-bold tracking-[0.14em] uppercase rtl:tracking-normal"
      :class="light ? 'glass-dark text-lagoon' : 'bg-brand/10 text-brand dark:bg-brand/15 dark:text-brand-soft'"
    >
      <span class="size-1.5 rounded-full bg-current" />
      {{ eyebrow }}
    </p>
    <component
      :is="as"
      v-reveal="60"
      class="text-3xl leading-[1.12] font-extrabold sm:text-4xl lg:text-[2.75rem]"
      :class="light ? 'text-white' : 'text-ink'"
    >
      <slot name="title">{{ title }}</slot>
    </component>
    <p v-if="subtitle" v-reveal="120" class="mt-4 text-base leading-relaxed sm:text-lg" :class="light ? 'text-white/70' : 'text-muted'">
      {{ subtitle }}
    </p>
  </div>
</template>
