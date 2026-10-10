<script setup lang="ts">
/** Dialog that slides up as a bottom sheet on phones and scales in on desktop. */
const open = defineModel<boolean>({ default: false })
withDefaults(defineProps<{ title?: string; size?: 'sm' | 'md' | 'lg' }>(), { size: 'md' })

const widths = { sm: 'sm:max-w-md', md: 'sm:max-w-xl', lg: 'sm:max-w-3xl' }

onKeyStroke('Escape', () => (open.value = false))
watch(open, (v) => {
  if (import.meta.client) document.documentElement.style.overflow = v ? 'hidden' : ''
})
onBeforeUnmount(() => {
  if (import.meta.client) document.documentElement.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <AnimatePresence>
      <div v-if="open" class="fixed inset-0 z-[80] flex items-end justify-center sm:items-center sm:p-6">
        <Motion
          as="div"
          class="absolute inset-0 bg-night-950/60 backdrop-blur-sm"
          :initial="{ opacity: 0 }"
          :animate="{ opacity: 1 }"
          :exit="{ opacity: 0 }"
          @click="open = false"
        />
        <Motion
          as="div"
          role="dialog"
          aria-modal="true"
          class="relative max-h-[92dvh] w-full overflow-y-auto rounded-t-3xl bg-elevated p-6 shadow-2xl safe-bottom sm:rounded-3xl sm:p-8"
          :class="widths[size]"
          :initial="{ opacity: 0, y: 40, scale: 0.98 }"
          :animate="{ opacity: 1, y: 0, scale: 1 }"
          :exit="{ opacity: 0, y: 30, scale: 0.98 }"
          :transition="{ type: 'spring', stiffness: 380, damping: 32 }"
        >
          <div class="mx-auto mb-4 h-1.5 w-10 rounded-full bg-line-strong sm:hidden" />
          <div class="mb-5 flex items-start justify-between gap-4">
            <h2 v-if="title" class="text-xl font-bold">{{ title }}</h2>
            <button type="button" class="-m-2 rounded-lg p-2 text-faint hover:bg-sunken hover:text-ink" :aria-label="$t('common.close')" @click="open = false">
              <AppIcon name="x" />
            </button>
          </div>
          <slot />
          <div v-if="$slots.footer" class="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <slot name="footer" />
          </div>
        </Motion>
      </div>
    </AnimatePresence>
  </Teleport>
</template>
