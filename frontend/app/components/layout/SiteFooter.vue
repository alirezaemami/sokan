<script setup lang="ts">
const year = new Date().getFullYear()
const columns = [
  {
    title: 'footer.shippers',
    links: [
      { to: '/get-quote', key: 'nav.getQuote' },
      { to: '/how-it-works', key: 'nav.howItWorks' },
      { to: '/forwarders', key: 'nav.forwarders' },
      { to: '/faq', key: 'nav.faq' },
    ],
  },
  {
    title: 'footer.forwarders',
    links: [
      { to: '/for-forwarders', key: 'nav.forForwarders' },
      { to: '/pricing', key: 'nav.pricing' },
      { to: '/register/forwarder', key: 'footer.joinNetwork' },
      { to: '/login', key: 'nav.login' },
    ],
  },
  {
    title: 'footer.company',
    links: [
      { to: '/about', key: 'nav.about' },
      { to: '/contact', key: 'nav.contact' },
      { to: '/terms', key: 'footer.terms' },
      { to: '/privacy', key: 'footer.privacy' },
    ],
  },
]
</script>

<template>
  <footer class="relative overflow-hidden bg-night-950 text-white">
    <div class="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-brand/60 to-transparent" />
    <div class="mx-auto max-w-7xl px-4 pt-16 pb-28 sm:px-6 lg:px-8 lg:pb-12">
      <div class="grid gap-12 lg:grid-cols-[1.4fr_repeat(3,1fr)]">
        <div>
          <AppLogo light />
          <p class="mt-5 max-w-sm text-sm leading-relaxed text-white/60">{{ $t('footer.tagline') }}</p>
          <div class="mt-6 flex flex-wrap gap-2">
            <span v-for="m in ['ship', 'plane', 'truck', 'train-front', 'zap']" :key="m" class="grid size-10 place-items-center rounded-xl bg-white/5 text-white/70 ring-1 ring-white/10">
              <AppIcon :name="m" :size="18" />
            </span>
          </div>
        </div>
        <div v-for="col in columns" :key="col.title">
          <h3 class="text-sm font-bold tracking-wide text-white/90">{{ $t(col.title) }}</h3>
          <ul class="mt-4 space-y-3">
            <li v-for="l in col.links" :key="l.to">
              <NuxtLinkLocale :to="l.to" class="text-sm text-white/55 transition-colors hover:text-lagoon">{{ $t(l.key) }}</NuxtLinkLocale>
            </li>
          </ul>
        </div>
      </div>
      <div class="mt-14 flex flex-col items-start justify-between gap-4 border-t border-white/8 pt-8 text-xs text-white/45 sm:flex-row sm:items-center">
        <p>© {{ year }} Sokan. {{ $t('footer.rights') }}</p>
        <div class="flex items-center gap-1">
          <LangSwitch light />
        </div>
      </div>
    </div>
  </footer>
</template>
