<script setup lang="ts">
/**
 * Marketing header. Transparent over the chart paper at the top of the
 * page, frosted once scrolled. The phone menu opens as a night chart.
 * A page whose hero is a night chart sets `definePageMeta({ headerTone:
 * 'night' })`; until scrolled, the header then draws light on night.
 */
const { y } = useWindowScroll()
const scrolled = computed(() => y.value > 16)
const menu = ref(false)
const route = useRoute()
const night = computed(() => route.meta.headerTone === 'night' && !scrolled.value)
const { isLoggedIn, homePath, me } = useAuth()

const links = [
  { to: '/how-it-works', key: 'nav.howItWorks' },
  { to: '/forwarders', key: 'nav.forwarders' },
  { to: '/for-forwarders', key: 'nav.forForwarders' },
  { to: '/pricing', key: 'nav.pricing' },
]

watch(() => route.fullPath, () => (menu.value = false))
watch(menu, (v) => {
  if (import.meta.client) document.documentElement.style.overflow = v ? 'hidden' : ''
})
// Navigating into a portal swaps the layout and unmounts the header before
// the watcher above can release the lock.
onBeforeUnmount(() => {
  if (import.meta.client) document.documentElement.style.overflow = ''
})
</script>

<template>
  <header class="fixed inset-x-0 top-0 z-50 transition-[background,border-color,box-shadow] duration-300" :class="scrolled ? 'glass border-x-0 border-t-0' : 'border-b border-transparent'">
    <div class="mx-auto flex h-[72px] max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
      <NuxtLinkLocale to="/" class="shrink-0" :aria-label="$t('nav.home')"><AppLogo :light="night" /></NuxtLinkLocale>

      <nav class="ms-6 hidden items-center gap-1 lg:flex" :aria-label="$t('nav.main')">
        <NuxtLinkLocale
          v-for="l in links"
          :key="l.to"
          :to="l.to"
          class="rounded-full px-3.5 py-2 text-[0.94rem] font-medium transition-colors"
          :class="night ? 'text-white/80 hover:text-white' : 'text-ink-soft hover:text-ink'"
          :active-class="night ? '!text-tide' : '!text-sea'"
        >
          {{ $t(l.key) }}
        </NuxtLinkLocale>
      </nav>

      <div class="ms-auto flex items-center gap-1">
        <div class="hidden items-center gap-1 sm:flex">
          <LangSwitch :light="night" />
          <ThemeToggle :light="night" />
        </div>
        <!-- Visibility lives on wrappers: AppButton's own inline-flex would beat a passed-in `hidden`. -->
        <div class="hidden sm:block">
          <ClientOnly>
            <AppButton v-if="isLoggedIn" :to="homePath" :variant="night ? 'night' : 'secondary'" size="sm" icon="dashboard">
              {{ me?.is_admin ? $t('nav.admin') : me?.forwarder ? $t('nav.partner') : $t('nav.account') }}
            </AppButton>
            <AppButton v-else to="/login" :variant="night ? 'night' : 'ghost'" size="sm">{{ $t('nav.login') }}</AppButton>
          </ClientOnly>
        </div>
        <div class="ms-1">
          <AppButton to="/get-quote" variant="accent" size="sm" icon-end="arrow-right">{{ $t('nav.getQuote') }}</AppButton>
        </div>
        <button
          type="button"
          class="grid size-11 place-items-center rounded-full lg:hidden"
          :class="night ? 'text-white hover:bg-white/10' : 'text-ink hover:bg-sunken'"
          :aria-label="$t('nav.menu')"
          :aria-expanded="menu"
          @click="menu = true"
        >
          <AppIcon name="menu" :size="24" />
        </button>
      </div>
    </div>

    <Teleport to="body">
      <AnimatePresence>
        <Motion
          v-if="menu"
          as="div"
          class="fixed inset-0 z-[70] flex flex-col overflow-y-auto bg-night-950 text-white lg:hidden"
          :initial="{ opacity: 0, clipPath: 'circle(0% at 100% 0%)' }"
          :animate="{ opacity: 1, clipPath: 'circle(150% at 100% 0%)' }"
          :exit="{ opacity: 0, clipPath: 'circle(0% at 100% 0%)' }"
          :transition="{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }"
        >
          <ChartBackground tone="night" compass />
          <div class="relative flex h-[72px] items-center justify-between px-4 sm:px-6">
            <AppLogo light />
            <button type="button" class="grid size-11 place-items-center rounded-full hover:bg-white/10" :aria-label="$t('common.close')" @click="menu = false">
              <AppIcon name="x" :size="26" />
            </button>
          </div>
          <nav class="relative flex flex-1 flex-col px-6 pt-6">
            <Motion
              v-for="(l, i) in [{ to: '/', key: 'nav.home' }, ...links, { to: '/about', key: 'nav.about' }, { to: '/contact', key: 'nav.contact' }]"
              :key="l.to"
              as="div"
              :initial="{ opacity: 0, x: 24 }"
              :animate="{ opacity: 1, x: 0 }"
              :transition="{ delay: 0.12 + i * 0.05, duration: 0.45 }"
            >
              <NuxtLinkLocale :to="l.to" class="font-display flex items-baseline gap-4 border-b border-tide/10 py-4 text-3xl text-white/90 hover:text-tide">
                <span class="chart-label text-tide/60">0{{ i + 1 }}</span>{{ $t(l.key) }}
              </NuxtLinkLocale>
            </Motion>
          </nav>
          <div class="relative flex flex-col gap-3 p-6 safe-bottom">
            <AppButton to="/get-quote" variant="accent" size="lg" block icon-end="arrow-right">{{ $t('nav.getQuote') }}</AppButton>
            <ClientOnly>
              <AppButton v-if="isLoggedIn" :to="homePath" variant="night" size="lg" block icon="dashboard">{{ $t('nav.dashboard') }}</AppButton>
              <AppButton v-else to="/login" variant="night" size="lg" block>{{ $t('nav.login') }}</AppButton>
            </ClientOnly>
            <div class="flex items-center justify-center gap-2 pt-2">
              <LangSwitch light />
              <ThemeToggle light />
            </div>
          </div>
        </Motion>
      </AnimatePresence>
    </Teleport>
  </header>
</template>
