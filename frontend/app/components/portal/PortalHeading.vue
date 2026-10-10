<script setup lang="ts">
defineProps<{ title: string; subtitle?: string; back?: string }>()
</script>

<template>
  <div class="mb-6 flex flex-wrap items-end justify-between gap-4 lg:mb-8">
    <div class="min-w-0">
      <NuxtLinkLocale v-if="back" :to="back" class="mb-2 inline-flex items-center gap-1 text-sm text-muted hover:text-ink">
        <AppIcon name="arrow-left" :size="16" flip /> {{ $t('common.back') }}
      </NuxtLinkLocale>
      <h1 class="font-display text-3xl text-ink sm:text-4xl">{{ title }}</h1>
      <p v-if="subtitle" class="mt-1 text-muted">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.default" class="flex flex-wrap gap-2"><slot /></div>
  </div>
</template>
