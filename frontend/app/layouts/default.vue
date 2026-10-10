<template>
  <div class="flex min-h-dvh flex-col">
    <SiteHeader />
    <main class="flex-1">
      <slot />
    </main>
    <SiteFooter />
    <MobileCta />
  </div>
</template>
