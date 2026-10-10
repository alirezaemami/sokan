<script setup lang="ts">
/**
 * One button for the whole app. Renders a locale-aware link when `to` is
 * set, a plain anchor for `href`, otherwise a <button>.
 */
const props = withDefaults(
  defineProps<{
    to?: string | Record<string, unknown>
    href?: string
    variant?: 'primary' | 'accent' | 'secondary' | 'ghost' | 'glass' | 'danger'
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
  'group relative inline-flex select-none items-center justify-center gap-2 whitespace-nowrap rounded-xl font-semibold transition-all duration-300 ease-[var(--ease-spring)] focus-visible:outline-2 disabled:pointer-events-none disabled:opacity-55 active:scale-[0.97]'

const variants: Record<string, string> = {
  primary:
    'bg-brand-gradient text-white shadow-[0_10px_30px_-10px_rgb(91_92_246/0.65)] hover:shadow-[0_16px_40px_-12px_rgb(91_92_246/0.8)] hover:-translate-y-0.5',
  accent:
    'bg-coral text-white shadow-[0_10px_30px_-10px_rgb(255_107_74/0.7)] hover:bg-coral-deep hover:-translate-y-0.5',
  secondary: 'bg-surface text-ink border border-line-strong hover:border-brand/40 hover:text-brand',
  ghost: 'text-ink-soft hover:bg-sunken hover:text-ink',
  glass: 'glass-dark text-white hover:bg-white/12',
  danger: 'bg-danger/10 text-danger hover:bg-danger hover:text-white',
}

const sizes: Record<string, string> = {
  sm: 'h-9 px-3.5 text-sm',
  md: 'h-11 px-5 text-[0.94rem]',
  lg: 'h-13 px-7 text-base',
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
