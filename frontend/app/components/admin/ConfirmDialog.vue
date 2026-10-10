<script setup lang="ts">
/**
 * Confirmation for consequential actions. With `reason`, the manager must
 * write one; it is shown to the affected company or customer.
 */
const open = defineModel<boolean>({ default: false })
const props = withDefaults(
  defineProps<{
    title: string
    text?: string
    confirmLabel: string
    variant?: 'primary' | 'accent' | 'danger'
    reason?: boolean
    reasonLabel?: string
    reasonHint?: string
    loading?: boolean
  }>(),
  { variant: 'primary', reason: false },
)
const emit = defineEmits<{ confirm: [reason: string] }>()
const reasonText = ref('')
watch(open, (v) => v && (reasonText.value = ''))
const ready = computed(() => !props.reason || reasonText.value.trim().length > 0)
</script>

<template>
  <AppModal v-model="open" :title="title" size="sm">
    <p v-if="props.text" class="text-sm leading-relaxed text-muted">{{ props.text }}</p>
    <FormField v-if="reason" v-model="reasonText" as="textarea" class="mt-4" :label="reasonLabel || $t('admin.reason')" :hint="reasonHint" required />
    <template #footer>
      <AppButton variant="ghost" @click="open = false">{{ $t('common.cancel') }}</AppButton>
      <AppButton :variant="variant" :loading="loading" :disabled="!ready" @click="emit('confirm', reasonText.trim())">{{ confirmLabel }}</AppButton>
    </template>
  </AppModal>
</template>
