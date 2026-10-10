<script setup lang="ts">
withDefaults(defineProps<{ light?: boolean }>(), { light: false })
const { dark, toggle } = useTheme()
</script>

<template>
  <button
    type="button"
    class="relative grid size-10 place-items-center overflow-hidden rounded-xl transition-colors"
    :class="light ? 'text-white/80 hover:bg-white/10 hover:text-white' : 'text-ink-soft hover:bg-sunken hover:text-ink'"
    :aria-label="$t('nav.theme')"
    @click="toggle"
  >
    <Transition
      enter-active-class="transition duration-500 ease-[var(--ease-spring)]"
      enter-from-class="opacity-0 rotate-90 scale-50"
      leave-active-class="transition duration-200 absolute"
      leave-to-class="opacity-0 -rotate-90 scale-50"
    >
      <AppIcon v-if="dark" key="sun" name="sun" :size="19" />
      <AppIcon v-else key="moon" name="moon" :size="19" />
    </Transition>
  </button>
</template>
