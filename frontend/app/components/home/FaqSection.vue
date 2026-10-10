<script setup lang="ts">
/**
 * FAQ accordion + FAQPage structured data. Questions live in the locale
 * files under `${group}.items` as { q, a } pairs.
 */
const props = withDefaults(defineProps<{ group?: string; count: number; title?: string }>(), { group: 'faq.general' })
const { t } = useI18n()
const open = ref<number | null>(0)

const items = computed(() =>
  Array.from({ length: props.count }, (_, i) => ({ q: t(`${props.group}.items.${i}.q`), a: t(`${props.group}.items.${i}.a`) })),
)

useSchemaOrg([
  defineWebPage({ '@type': 'FAQPage' }),
  ...items.value.map((it) => defineQuestion({ name: it.q, acceptedAnswer: it.a })),
])
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <div class="space-y-3">
      <div v-for="(it, i) in items" :key="i" v-reveal="i * 50" class="card overflow-hidden">
        <h3>
          <button
            type="button"
            class="flex w-full items-center justify-between gap-4 px-6 py-5 text-start font-bold"
            :aria-expanded="open === i"
            @click="open = open === i ? null : i"
          >
            {{ it.q }}
            <span class="grid size-8 shrink-0 place-items-center rounded-full bg-sunken transition-transform duration-300" :class="open === i && 'rotate-45 bg-helm text-helm-ink'">
              <AppIcon name="plus" :size="16" />
            </span>
          </button>
        </h3>
        <div class="grid transition-[grid-template-rows] duration-400 ease-[var(--ease-spring)]" :class="open === i ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'">
          <div class="overflow-hidden">
            <p class="px-6 pb-6 leading-relaxed text-muted">{{ it.a }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
