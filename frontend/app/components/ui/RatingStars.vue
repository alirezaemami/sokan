<script setup lang="ts">
const model = defineModel<number>({ default: 0 })
withDefaults(defineProps<{ readonly?: boolean; size?: number }>(), { readonly: true, size: 16 })
const hover = ref(0)
</script>

<template>
  <div class="inline-flex items-center gap-0.5" :role="readonly ? 'img' : 'radiogroup'" :aria-label="`${model} / 5`">
    <component
      :is="readonly ? 'span' : 'button'"
      v-for="i in 5"
      :key="i"
      :type="readonly ? undefined : 'button'"
      :class="[!readonly && 'transition-transform hover:scale-125', (hover || model) >= i - 0.25 ? 'text-warning' : 'text-line-strong']"
      :aria-label="readonly ? undefined : `${i}`"
      @mouseenter="!readonly && (hover = i)"
      @mouseleave="!readonly && (hover = 0)"
      @click="!readonly && (model = i)"
    >
      <AppIcon name="star" :size="size" class="fill-current" />
    </component>
  </div>
</template>
