<script setup lang="ts">
const model = defineModel<string>({ default: '' })
defineProps<{ options: { value: string; label: string; count?: number }[] }>()
</script>

<template>
  <div class="no-scrollbar -mx-4 mb-5 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:px-0">
    <button
      v-for="o in options"
      :key="o.value"
      type="button"
      class="inline-flex shrink-0 items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-all"
      :class="model === o.value ? 'bg-ink text-bg shadow-md' : 'bg-surface text-ink-soft ring-1 ring-line hover:ring-line-strong'"
      @click="model = o.value"
    >
      {{ o.label }}
      <span v-if="o.count != null" class="rounded-md px-1.5 text-xs" :class="model === o.value ? 'bg-bg/20' : 'bg-sunken'">{{ o.count }}</span>
    </button>
  </div>
</template>
