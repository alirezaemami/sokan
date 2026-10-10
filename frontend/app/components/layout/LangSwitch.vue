<script setup lang="ts">
withDefaults(defineProps<{ light?: boolean }>(), { light: false })
const { locale, locales } = useI18n()
const switchLocalePath = useSwitchLocalePath()
const other = computed(() => locales.value.find((l) => l.code !== locale.value))
</script>

<template>
  <NuxtLink
    v-if="other"
    :to="switchLocalePath(other.code)"
    class="inline-flex h-10 items-center gap-1.5 rounded-xl px-3 text-sm font-semibold transition-colors"
    :class="light ? 'text-white/80 hover:bg-white/10 hover:text-white' : 'text-ink-soft hover:bg-sunken hover:text-ink'"
    :hreflang="other.language"
    :lang="other.language"
  >
    <AppIcon name="languages" :size="18" />
    <span>{{ other.name }}</span>
  </NuxtLink>
</template>
