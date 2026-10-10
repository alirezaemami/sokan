import Lenis from 'lenis'

/**
 * Smooth wheel scrolling on desktop.
 *
 * Skipped under reduced motion and on touch devices — hijacking momentum
 * scroll on a phone feels broken, and mobile browsers already scroll well.
 * Also skipped inside the portals, where dense tables and nested scroll
 * areas fight with it.
 */
export default defineNuxtPlugin((nuxtApp) => {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const coarse = window.matchMedia('(pointer: coarse)').matches
  if (reduced || coarse) return

  const lenis = new Lenis({ duration: 1.05, smoothWheel: true })
  let frame = 0
  const raf = (time: number) => {
    lenis.raf(time)
    frame = requestAnimationFrame(raf)
  }
  frame = requestAnimationFrame(raf)

  const router = useRouter()
  const sync = () => {
    const portal = /\/(account|partner)(\/|$)/.test(router.currentRoute.value.path)
    portal ? lenis.stop() : lenis.start()
  }
  sync()

  nuxtApp.hook('page:finish', () => {
    sync()
    if (!router.currentRoute.value.hash) lenis.scrollTo(0, { immediate: true })
  })
  // Lives as long as the page does; tidy up only on a hot reload.
  import.meta.hot?.dispose(() => {
    cancelAnimationFrame(frame)
    lenis.destroy()
  })

  return { provide: { lenis } }
})
