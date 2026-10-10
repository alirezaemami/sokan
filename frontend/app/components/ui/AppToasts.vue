<script setup lang="ts">
const { toasts, dismiss } = useToast()
const icons = { success: 'circle-check', error: 'alert', info: 'info' }
const tones = { success: 'text-success', error: 'text-danger', info: 'text-brand' }
</script>

<template>
  <div class="pointer-events-none fixed inset-x-0 bottom-20 z-[90] flex flex-col items-center gap-2 px-4 sm:bottom-6 sm:items-end sm:px-6" aria-live="polite">
    <TransitionGroup
      enter-active-class="transition duration-300 ease-[var(--ease-spring)]"
      enter-from-class="translate-y-4 opacity-0 scale-95"
      leave-active-class="transition duration-200"
      leave-to-class="opacity-0 translate-y-2"
    >
      <div
        v-for="t in toasts"
        :key="t.id"
        class="glass pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-2xl p-4 shadow-xl"
      >
        <AppIcon :name="icons[t.kind]" :class="tones[t.kind]" class="mt-0.5 shrink-0" />
        <p class="flex-1 text-sm leading-relaxed text-ink">{{ t.text }}</p>
        <button type="button" class="text-faint hover:text-ink" :aria-label="$t('common.close')" @click="dismiss(t.id)">
          <AppIcon name="x" :size="16" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>
