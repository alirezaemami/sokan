<script setup lang="ts">
/**
 * Card that tilts toward the pointer with a moving glare. Desktop pointers
 * only — on touch it's a plain card.
 */
const el = ref<HTMLElement | null>(null)
const style = ref<Record<string, string>>({})
let fine = false

onMounted(() => {
  fine = window.matchMedia('(pointer: fine)').matches && !window.matchMedia('(prefers-reduced-motion: reduce)').matches
})

function move(e: PointerEvent) {
  if (!fine || !el.value) return
  const r = el.value.getBoundingClientRect()
  const x = (e.clientX - r.left) / r.width
  const y = (e.clientY - r.top) / r.height
  style.value = {
    transform: `perspective(900px) rotateX(${(0.5 - y) * 7}deg) rotateY(${(x - 0.5) * 9}deg) translateZ(0)`,
    '--gx': `${x * 100}%`,
    '--gy': `${y * 100}%`,
  }
}

function leave() {
  style.value = { transform: 'perspective(900px) rotateX(0) rotateY(0)' }
}
</script>

<template>
  <div
    ref="el"
    class="group/tilt relative transition-transform duration-500 ease-[var(--ease-spring)] will-change-transform"
    :style="style"
    @pointermove="move"
    @pointerleave="leave"
  >
    <slot />
    <div
      class="pointer-events-none absolute inset-0 rounded-[inherit] opacity-0 transition-opacity duration-300 group-hover/tilt:opacity-100"
      style="background: radial-gradient(500px circle at var(--gx, 50%) var(--gy, 50%), rgb(255 255 255 / 0.12), transparent 40%)"
    />
  </div>
</template>
