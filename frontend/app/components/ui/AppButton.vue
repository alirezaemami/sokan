<script setup lang="ts">
/**
 * One button for the whole app. Renders a locale-aware link when `to` is
 * set, a plain anchor for `href`, otherwise a <button>.
 */
const props = withDefaults(
  defineProps<{
    to?: string | Record<string, unknown>
    href?: string
    variant?: 'primary' | 'accent' | 'secondary' | 'ghost' | 'night' | 'danger'
    size?: 'sm' | 'md' | 'lg'
    icon?: string
    iconEnd?: string
    loading?: boolean
    disabled?: boolean
    block?: boolean
    type?: 'button' | 'submit'
  }>(),
  { variant: 'primary', size: 'md', type: 'button' },
)

const base =
  'group relative inline-flex select-none items-center justify-center gap-2 whitespace-nowrap rounded-full font-semibold transition-all duration-300 ease-[var(--ease-spring)] focus-visible:outline-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.97]'

// Chart Room: navy chart ink for primary, buoy red for the one key action
// per screen, outlined for secondary. `night` sits on night-chart surfaces.
const variants: Record<string, string> = {
  primary: 'bg-helm text-helm-ink hover:bg-ink-soft',
  accent: 'bg-buoy text-white shadow-[0_10px_24px_-12px_rgb(192_57_43/0.7)] hover:bg-buoy-deep',
  secondary: 'border border-line-strong bg-surface text-ink hover:border-sea hover:text-sea',
  ghost: 'text-ink-soft hover:bg-sunken hover:text-ink',
  night: 'border border-tide/30 text-white hover:border-tide hover:bg-tide/10',
  danger: 'bg-danger/10 text-danger hover:bg-danger hover:text-white',
}

const sizes: Record<string, string> = {
  sm: 'h-9 px-4 text-sm',
  md: 'h-11 px-5 text-[0.94rem]',
  lg: 'h-12 px-7 text-base',
}

const cls = computed(() => [base, variants[props.variant], sizes[props.size], props.block && 'w-full'])
const iconSize = computed(() => (props.size === 'sm' ? 16 : 18))
const DIRECTIONAL = ['arrow-right', 'arrow-left', 'chevron-right', 'chevron-left', 'arrow-up-right']
</script>

<template>
  <NuxtLinkLocale v-if="to" :to="to" :class="cls">
    <AppIcon v-if="icon" :name="icon" :size="iconSize" :flip="DIRECTIONAL.includes(icon)" />
    <slot />
    <AppIcon
      v-if="iconEnd"
      :name="iconEnd"
      :size="iconSize"
      :flip="DIRECTIONAL.includes(iconEnd)"
      class="transition-transform duration-300 group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5"
    />
  </NuxtLinkLocale>
  <a v-else-if="href" :href="href" :class="cls" target="_blank" rel="noopener">
    <AppIcon v-if="icon" :name="icon" :size="iconSize" />
    <slot />
    <AppIcon v-if="iconEnd" :name="iconEnd" :size="iconSize" />
  </a>
  <button v-else :type="type" :class="cls" :disabled="disabled || loading" :aria-busy="loading || undefined">
    <AppIcon v-if="loading" name="loader" :size="iconSize" class="animate-spin" />
    <AppIcon v-else-if="icon" :name="icon" :size="iconSize" :flip="DIRECTIONAL.includes(icon)" />
    <slot />
    <AppIcon
      v-if="iconEnd && !loading"
      :name="iconEnd"
      :size="iconSize"
      :flip="DIRECTIONAL.includes(iconEnd)"
      class="transition-transform duration-300 group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5"
    />
  </button>
</template>
