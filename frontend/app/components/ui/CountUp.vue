<script setup lang="ts">
/** Animated number that counts up once it scrolls into view. SSR renders the final value. */
const props = withDefaults(defineProps<{ to: number; duration?: number; suffix?: string; compact?: boolean }>(), {
  duration: 1600,
  suffix: '',
  compact: false,
})

const fmt = useFormat()
const el = ref<HTMLElement | null>(null)
const value = ref(props.to)
let started = false

function run() {
  if (started) return
  started = true
  const start = performance.now()
  const tick = (now: number) => {
    const p = Math.min((now - start) / props.duration, 1)
    value.value = Math.round(props.to * (1 - Math.pow(1 - p, 4)))
    if (p < 1) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}

onMounted(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !props.to) return
  value.value = 0
  useIntersectionObserver(el, ([entry]) => entry?.isIntersecting && run(), { threshold: 0.4 })
})

watch(
  () => props.to,
  (v) => {
    if (started || !el.value) value.value = v
  },
)
</script>

<template>
  <span ref="el" class="tabular-nums">{{ compact ? fmt.compact(value) : fmt.number(value) }}{{ suffix }}</span>
</template>
