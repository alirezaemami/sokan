import Lenis from 'lenis'

/**
 * Smooth wheel scrolling on desktop.
 *
 * Skipped under reduced motion and on touch devices — hijacking momentum
 * scroll on a phone feels broken, and mobile browsers already scroll well.
 * Also skipped inside the portals, where dense tables and nested scroll
 * areas fight with it. There it is destroyed, not stopped: a stopped Lenis
 * cancels every wheel event, which locks the page.
 */
export default defineNuxtPlugin((nuxtApp) => {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const coarse = window.matchMedia('(pointer: coarse)').matches
  if (reduced || coarse) return

  let lenis: Lenis | null = null
  let frame = 0
  const raf = (time: number) => {
    lenis?.raf(time)
    frame = requestAnimationFrame(raf)
  }

  function enable() {
    if (lenis) return
    lenis = new Lenis({ duration: 1.05, smoothWheel: true })
    frame = requestAnimationFrame(raf)
  }

  function disable() {
    cancelAnimationFrame(frame)
    lenis?.destroy()
    lenis = null
  }

  const router = useRouter()
  const sync = () => {
    const portal = /\/(account|partner)(\/|$)/.test(router.currentRoute.value.path)
    portal ? disable() : enable()
  }
  sync()

  nuxtApp.hook('page:finish', () => {
    sync()
    if (!router.currentRoute.value.hash) lenis?.scrollTo(0, { immediate: true })
  })
  // Lives as long as the page does; tidy up only on a hot reload.
  import.meta.hot?.dispose(disable)
})
