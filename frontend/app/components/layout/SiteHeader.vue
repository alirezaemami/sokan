<script setup lang="ts">
/**
 * Marketing header. Transparent with light text over the dark hero every
 * marketing page opens with, then frosted glass once the page scrolls.
 */
const { y } = useWindowScroll()
const scrolled = computed(() => y.value > 24)
const menu = ref(false)
const route = useRoute()
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
</script>

<template>
  <header
    class="fixed inset-x-0 top-0 z-50 transition-all duration-500"
    :class="scrolled ? 'glass border-x-0 border-t-0 shadow-[0_8px_30px_-18px_rgb(0_0_0/0.35)]' : 'border-b border-transparent'"
  >
    <div class="mx-auto flex h-[72px] max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
      <NuxtLinkLocale to="/" class="shrink-0" :aria-label="$t('nav.home')">
        <AppLogo :light="!scrolled" />
      </NuxtLinkLocale>

      <nav class="ms-6 hidden items-center gap-1 lg:flex" :aria-label="$t('nav.main')">
        <NuxtLinkLocale
          v-for="l in links"
          :key="l.to"
          :to="l.to"
          class="relative rounded-lg px-3.5 py-2 text-[0.94rem] font-semibold transition-colors"
          :class="scrolled ? 'text-ink-soft hover:text-ink' : 'text-white/75 hover:text-white'"
          active-class="!text-brand dark:!text-brand-soft"
        >
          {{ $t(l.key) }}
        </NuxtLinkLocale>
      </nav>

      <div class="ms-auto flex items-center gap-1">
        <div class="hidden items-center gap-1 sm:flex">
          <LangSwitch :light="!scrolled" />
          <ThemeToggle :light="!scrolled" />
        </div>
        <!-- Visibility lives on wrappers: AppButton's own inline-flex would beat a passed-in `hidden`. -->
        <div class="hidden sm:block">
          <ClientOnly>
            <AppButton v-if="isLoggedIn" :to="homePath" :variant="scrolled ? 'secondary' : 'glass'" size="sm" icon="dashboard">
              {{ me?.forwarder ? $t('nav.partner') : $t('nav.account') }}
            </AppButton>
            <AppButton v-else to="/login" :variant="scrolled ? 'ghost' : 'glass'" size="sm">
              {{ $t('nav.login') }}
            </AppButton>
          </ClientOnly>
        </div>
        <div class="ms-1">
          <AppButton to="/get-quote" variant="accent" size="sm" icon-end="arrow-right">
            {{ $t('nav.getQuote') }}
          </AppButton>
        </div>
        <button
          type="button"
          class="grid size-11 place-items-center rounded-xl lg:hidden"
          :class="scrolled ? 'text-ink hover:bg-sunken' : 'text-white hover:bg-white/10'"
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
          <AuroraBackground />
          <div class="relative flex h-[72px] items-center justify-between px-4 sm:px-6">
            <AppLogo light />
            <button type="button" class="grid size-11 place-items-center rounded-xl hover:bg-white/10" :aria-label="$t('common.close')" @click="menu = false">
              <AppIcon name="x" :size="26" />
            </button>
          </div>
          <nav class="relative flex flex-1 flex-col gap-1 px-6 pt-6">
            <Motion
              v-for="(l, i) in [{ to: '/', key: 'nav.home' }, ...links, { to: '/about', key: 'nav.about' }, { to: '/contact', key: 'nav.contact' }]"
              :key="l.to"
              as="div"
              :initial="{ opacity: 0, x: 24 }"
              :animate="{ opacity: 1, x: 0 }"
              :transition="{ delay: 0.12 + i * 0.05, duration: 0.45 }"
            >
              <NuxtLinkLocale :to="l.to" class="block border-b border-white/8 py-4 text-2xl font-bold tracking-tight text-white/90 hover:text-lagoon">
                {{ $t(l.key) }}
              </NuxtLinkLocale>
            </Motion>
          </nav>
          <div class="relative flex flex-col gap-3 p-6 safe-bottom">
            <AppButton to="/get-quote" variant="accent" size="lg" block icon-end="arrow-right">{{ $t('nav.getQuote') }}</AppButton>
            <ClientOnly>
              <AppButton v-if="isLoggedIn" :to="homePath" variant="glass" size="lg" block icon="dashboard">{{ $t('nav.dashboard') }}</AppButton>
              <AppButton v-else to="/login" variant="glass" size="lg" block>{{ $t('nav.login') }}</AppButton>
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
