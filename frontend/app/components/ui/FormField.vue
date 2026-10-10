<script setup lang="ts">
/**
 * Labelled input. Pass `as="textarea"` or `as="select"` (with <option> slot),
 * or use the default slot for a custom control.
 */
const model = defineModel<string | number | null | undefined>()

const props = withDefaults(
  defineProps<{
    label?: string
    hint?: string
    error?: string | null
    as?: 'input' | 'textarea' | 'select'
    type?: string
    placeholder?: string
    required?: boolean
    icon?: string
    suffix?: string
    min?: number | string
    max?: number | string
    step?: number | string
    rows?: number
    autocomplete?: string
    inputmode?: 'text' | 'numeric' | 'decimal' | 'email' | 'tel' | 'url' | 'search'
    dir?: 'ltr' | 'rtl' | 'auto'
  }>(),
  { as: 'input', type: 'text', rows: 4 },
)

const id = useId()
const control =
  'w-full rounded-xl border bg-surface text-ink placeholder:text-faint transition-[border-color,box-shadow] duration-200 outline-none focus:border-brand focus:ring-4 focus:ring-[var(--ring)]'
const cls = computed(() => [
  control,
  props.error ? 'border-danger/60' : 'border-line-strong',
  props.as === 'textarea' ? 'px-4 py-3 leading-relaxed' : 'h-12 px-4',
  props.icon && 'ps-11',
  props.suffix && 'pe-14',
])
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="id" class="text-sm font-semibold text-ink-soft">
      {{ label }}<span v-if="required" class="text-coral"> *</span>
    </label>
    <div class="relative">
      <AppIcon v-if="icon" :name="icon" :size="18" class="pointer-events-none absolute start-4 top-1/2 -translate-y-1/2 text-faint" />
      <slot :id="id" :cls="cls">
        <textarea
          v-if="as === 'textarea'"
          :id="id"
          v-model="model as string"
          :class="cls"
          :rows="rows"
          :placeholder="placeholder"
          :required="required"
          :dir="dir"
        />
        <select v-else-if="as === 'select'" :id="id" v-model="model" :class="[cls, 'appearance-none pe-10']" :required="required">
          <slot name="options" />
        </select>
        <input
          v-else
          :id="id"
          v-model="model"
          :class="cls"
          :type="type"
          :placeholder="placeholder"
          :required="required"
          :min="min"
          :max="max"
          :step="step"
          :autocomplete="autocomplete"
          :inputmode="inputmode"
          :dir="dir"
        />
      </slot>
      <AppIcon
        v-if="as === 'select'"
        name="chevron-down"
        :size="18"
        class="pointer-events-none absolute end-4 top-1/2 -translate-y-1/2 text-faint"
      />
      <span v-if="suffix" class="pointer-events-none absolute end-4 top-1/2 -translate-y-1/2 text-sm font-medium text-faint">{{ suffix }}</span>
    </div>
    <p v-if="error" class="text-sm text-danger">{{ error }}</p>
    <p v-else-if="hint" class="text-xs text-faint">{{ hint }}</p>
  </div>
</template>
