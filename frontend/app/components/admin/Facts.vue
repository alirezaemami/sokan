<script setup lang="ts">
/** Label/value pairs for detail pages. Empty values show a dash. */
defineProps<{ items: { label: string; value?: string | number | null; href?: string }[] }>()
</script>

<template>
  <dl class="grid gap-x-6 gap-y-4 sm:grid-cols-2">
    <div v-for="f in items" :key="f.label" class="min-w-0">
      <dt class="text-xs font-medium text-faint">{{ f.label }}</dt>
      <dd class="mt-0.5 text-sm break-words text-ink">
        <a v-if="f.href && f.value" :href="f.href" target="_blank" rel="noopener" class="text-sea hover:underline">{{ f.value }}</a>
        <template v-else>{{ f.value === 0 ? 0 : f.value || '—' }}</template>
      </dd>
    </div>
  </dl>
</template>
