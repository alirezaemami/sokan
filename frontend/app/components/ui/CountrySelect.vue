<script setup lang="ts">
/**
 * Searchable country combobox. Values are Frappe Country names (English);
 * labels are localised through Intl.DisplayNames, and search matches both.
 */
import type { Country } from '~/types/sokan'

const model = defineModel<string | null | undefined>()
const props = withDefaults(defineProps<{ label?: string; placeholder?: string; required?: boolean; error?: string | null }>(), {})

const fmt = useFormat()
const countries = useCountries()
const open = ref(false)
const query = ref('')
const root = ref<HTMLElement | null>(null)
const input = ref<HTMLInputElement | null>(null)
const active = ref(0)
const id = useId()

const options = computed(() =>
  countries.value.map((c) => ({ ...c, label: fmt.country(c.code, c.name) })).sort((a, b) => a.label.localeCompare(b.label)),
)
const selected = computed(() => options.value.find((o) => o.name === model.value))
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  const list = q ? options.value.filter((o) => o.label.toLowerCase().includes(q) || o.name.toLowerCase().includes(q)) : options.value
  return list.slice(0, 80)
})

watch(query, () => (active.value = 0))

function choose(name: string) {
  model.value = name
  open.value = false
  query.value = ''
}

function openList() {
  open.value = true
  nextTick(() => input.value?.focus())
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowDown') {
    active.value = Math.min(active.value + 1, filtered.value.length - 1)
    e.preventDefault()
  } else if (e.key === 'ArrowUp') {
    active.value = Math.max(active.value - 1, 0)
    e.preventDefault()
  } else if (e.key === 'Enter') {
    const o = filtered.value[active.value]
    if (o) choose(o.name)
    e.preventDefault()
  } else if (e.key === 'Escape') {
    open.value = false
  }
}

onClickOutside(root, () => (open.value = false))
</script>

<template>
  <div ref="root" class="relative flex flex-col gap-1.5">
    <label v-if="label" :for="id" class="text-sm font-semibold text-ink-soft">
      {{ label }}<span v-if="required" class="text-coral"> *</span>
    </label>
    <button
      :id="id"
      type="button"
      class="flex h-12 w-full items-center gap-3 rounded-xl border bg-surface px-4 text-start transition-[border-color,box-shadow] outline-none focus:border-brand focus:ring-4 focus:ring-[var(--ring)]"
      :class="error ? 'border-danger/60' : 'border-line-strong'"
      :aria-expanded="open"
      aria-haspopup="listbox"
      @click="openList"
    >
      <span class="text-lg leading-none">{{ fmt.flag(selected?.code) }}</span>
      <span class="flex-1 truncate" :class="selected ? 'text-ink' : 'text-faint'">{{ selected?.label || placeholder || $t('common.selectCountry') }}</span>
      <AppIcon name="chevron-down" :size="18" class="text-faint transition-transform" :class="open && 'rotate-180'" />
    </button>
    <p v-if="error" class="text-sm text-danger">{{ error }}</p>

    <Transition name="fade">
      <div v-if="open" class="card absolute inset-x-0 top-full z-40 mt-2 overflow-hidden p-2 shadow-2xl">
        <div class="relative">
          <AppIcon name="search" :size="16" class="pointer-events-none absolute start-3 top-1/2 -translate-y-1/2 text-faint" />
          <input
            ref="input"
            v-model="query"
            type="search"
            class="h-10 w-full rounded-lg bg-sunken ps-9 pe-3 text-sm outline-none"
            :placeholder="$t('common.search')"
            @keydown="onKey"
          />
        </div>
        <ul role="listbox" class="mt-2 max-h-64 overflow-y-auto overscroll-contain">
          <li
            v-for="(o, i) in filtered"
            :key="o.name"
            role="option"
            :aria-selected="o.name === model"
            class="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm"
            :class="[i === active ? 'bg-brand/10 text-brand' : 'text-ink-soft', o.name === model && 'font-semibold']"
            @mouseenter="active = i"
            @click="choose(o.name)"
          >
            <span class="text-base">{{ fmt.flag(o.code) }}</span>
            <span class="flex-1 truncate">{{ o.label }}</span>
            <AppIcon v-if="o.name === model" name="check" :size="16" />
          </li>
          <li v-if="!filtered.length" class="px-3 py-6 text-center text-sm text-faint">{{ $t('common.noResults') }}</li>
        </ul>
      </div>
    </Transition>
  </div>
</template>
