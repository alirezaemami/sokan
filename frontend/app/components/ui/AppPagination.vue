<script setup lang="ts">
const page = defineModel<number>({ default: 1 })
const props = defineProps<{ total: number; pageSize: number }>()
const pages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const fmt = useFormat()
</script>

<template>
  <nav v-if="pages > 1" class="flex items-center justify-center gap-2" :aria-label="$t('common.pagination')">
    <AppButton variant="secondary" size="sm" icon="chevron-left" :disabled="page <= 1" @click="page--">
      <span class="sr-only">{{ $t('common.previous') }}</span>
    </AppButton>
    <span class="px-3 text-sm text-muted">{{ $t('common.pageOf', { page: fmt.number(page), pages: fmt.number(pages) }) }}</span>
    <AppButton variant="secondary" size="sm" icon="chevron-right" :disabled="page >= pages" @click="page++">
      <span class="sr-only">{{ $t('common.next') }}</span>
    </AppButton>
  </nav>
</template>
