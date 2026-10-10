<script setup lang="ts">
/** Sticky "get quotes" bar on phones, shown once the hero CTA has scrolled away. */
const { y } = useWindowScroll()
const route = useRoute()
const hidden = computed(() => /get-quote|register|login/.test(route.path))
const show = computed(() => y.value > 520 && !hidden.value)
</script>

<template>
  <Transition
    enter-active-class="transition duration-500 ease-[var(--ease-spring)]"
    enter-from-class="translate-y-full"
    leave-active-class="transition duration-300"
    leave-to-class="translate-y-full"
  >
    <div v-if="show" class="glass fixed inset-x-0 bottom-0 z-40 border-x-0 border-b-0 px-4 pt-3 safe-bottom md:hidden">
      <AppButton to="/get-quote" variant="accent" size="lg" block icon-end="arrow-right">{{ $t('nav.getQuoteFree') }}</AppButton>
    </div>
  </Transition>
</template>
