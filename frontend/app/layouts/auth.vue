<script setup lang="ts">
/** Split screen: brand story on the left (desktop), the form on the right. */
</script>

<template>
  <div class="grid min-h-dvh lg:grid-cols-[1.05fr_1fr]">
    <aside class="relative hidden overflow-hidden bg-night-950 p-12 text-white lg:flex lg:flex-col">
      <AuroraBackground />
      <NuxtLinkLocale to="/" class="relative"><AppLogo light /></NuxtLinkLocale>
      <div class="relative my-auto max-w-md">
        <RouteGlobe class="mb-10 w-full max-w-sm opacity-90" />
        <h2 class="text-3xl leading-tight font-extrabold">{{ $t('auth.sideTitle') }}</h2>
        <p class="mt-4 text-white/65">{{ $t('auth.sideText') }}</p>
        <ul class="mt-8 space-y-3 text-sm text-white/80">
          <li v-for="k in ['auth.side1', 'auth.side2', 'auth.side3']" :key="k" class="flex items-center gap-3">
            <span class="grid size-6 place-items-center rounded-full bg-lagoon/20 text-lagoon"><AppIcon name="check" :size="14" /></span>
            {{ $t(k) }}
          </li>
        </ul>
      </div>
    </aside>
    <main class="relative flex flex-col">
      <div class="flex h-18 items-center justify-between px-5 sm:px-8">
        <NuxtLinkLocale to="/" class="lg:invisible"><AppLogo /></NuxtLinkLocale>
        <div class="flex items-center gap-1">
          <LangSwitch />
          <ThemeToggle />
        </div>
      </div>
      <div class="flex flex-1 items-start justify-center px-5 pt-4 pb-16 sm:items-center sm:px-8">
        <div class="w-full max-w-md">
          <slot />
        </div>
      </div>
    </main>
  </div>
</template>
