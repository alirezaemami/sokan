/**
 * `v-reveal` — fade/slide an element in the first time it enters the viewport.
 *
 * Registered universally: Vue's SSR renderer looks every directive up while
 * serialising, and a browser-only directive would crash the render. On the
 * server it adds nothing, so markup ships fully visible — crawlers and no-JS
 * visitors read the page normally. The hidden state is applied only once JS
 * is running to take it back off.
 *
 * Usage:  <div v-reveal>         immediate
 *         <div v-reveal="120">   120ms stagger delay
 */
export default defineNuxtPlugin((nuxtApp) => {
  let observer: IntersectionObserver | null = null

  if (import.meta.client && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue
          entry.target.setAttribute('data-reveal', 'in')
          observer!.unobserve(entry.target)
        }
      },
      { rootMargin: '0px 0px -10% 0px', threshold: 0.08 },
    )
  }

  nuxtApp.vueApp.directive('reveal', {
    getSSRProps: () => ({}),
    mounted(el: HTMLElement, binding) {
      if (!observer) return
      const delay = Number(binding.value) || 0
      if (delay) el.style.setProperty('--reveal-delay', `${delay}ms`)
      el.setAttribute('data-reveal', '')
      requestAnimationFrame(() => observer!.observe(el))
    },
    unmounted(el: HTMLElement) {
      observer?.unobserve(el)
    },
  })
})
