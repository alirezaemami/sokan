/**
 * Scroll parallax: sets `--parallax` (px) on the element as it crosses the
 * viewport, from +range below to -range above. Style the moving child with
 * `translate: 0 var(--parallax)` and oversize it so its edges never show.
 * Off under reduced motion and until the page is interactive.
 */
export function useParallax(target: Ref<HTMLElement | null>, range = 60) {
  if (import.meta.server) return
  let frame = 0
  const update = () => {
    frame = 0
    const el = target.value
    if (!el) return
    const r = el.getBoundingClientRect()
    const vh = window.innerHeight
    if (r.bottom < 0 || r.top > vh) return
    // -1 when the element's centre is at the bottom of the screen, +1 at the top.
    const progress = ((r.top + r.height / 2) / vh) * 2 - 1
    el.style.setProperty('--parallax', `${(progress * range).toFixed(1)}px`)
  }
  const onScroll = () => {
    if (!frame) frame = requestAnimationFrame(update)
  }
  onMounted(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    update()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll, { passive: true })
  })
  onBeforeUnmount(() => {
    cancelAnimationFrame(frame)
    window.removeEventListener('scroll', onScroll)
    window.removeEventListener('resize', onScroll)
  })
}
