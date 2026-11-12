<script setup lang="ts">
/**
 * Company, contact and trust-badge details from app.config (`trust`).
 * Each empty item is skipped, and the whole block stays hidden until at
 * least one item has real content, so no placeholder ever reaches the page.
 */
const trust = useAppConfig().trust

const messengers = computed(() => trust.messengers.filter((m) => m.name && m.url))
const hasAny = computed(
  () => Boolean(trust.companyName || trust.address || trust.phone || trust.email || trust.badgeHtml || trust.showAbout) || messengers.value.length > 0,
)
</script>

<template>
  <section v-if="hasAny" class="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
    <div class="card grid gap-8 p-7 sm:p-9 lg:grid-cols-[1fr_auto] lg:items-center">
      <div>
        <h2 class="font-display text-2xl text-ink sm:text-3xl">{{ $t('home.trust.title') }}</h2>
        <p v-if="trust.companyName" class="mt-3 font-semibold text-ink">{{ trust.companyName }}</p>
        <p v-if="trust.address" class="mt-1 flex items-start gap-2 text-sm text-muted">
          <AppIcon name="map-pin" :size="16" class="mt-0.5 shrink-0" /> {{ trust.address }}
        </p>
        <ul class="mt-5 flex flex-wrap gap-x-6 gap-y-3 text-sm">
          <li v-if="trust.phone">
            <a :href="`tel:${trust.phone.replace(/\s+/g, '')}`" class="inline-flex items-center gap-2 font-semibold text-sea" dir="ltr">
              <AppIcon name="phone" :size="16" /> {{ trust.phone }}
            </a>
          </li>
          <li v-if="trust.email">
            <a :href="`mailto:${trust.email}`" class="inline-flex items-center gap-2 font-semibold text-sea" dir="ltr">
              <AppIcon name="mail" :size="16" /> {{ trust.email }}
            </a>
          </li>
          <li v-for="m in messengers" :key="m.url">
            <a :href="m.url" target="_blank" rel="noopener" class="inline-flex items-center gap-2 font-semibold text-sea">
              <AppIcon name="message" :size="16" /> {{ m.name }}
            </a>
          </li>
          <li v-if="trust.showAbout">
            <NuxtLinkLocale to="/about" class="inline-flex items-center gap-1.5 font-semibold text-sea">
              {{ $t('nav.about') }} <AppIcon name="arrow-right" :size="15" flip />
            </NuxtLinkLocale>
          </li>
        </ul>
      </div>
      <!-- Badge embed code is supplied by the issuer (e.g. Enamad) and set in app.config only. -->
      <div v-if="trust.badgeHtml" class="justify-self-start lg:justify-self-end" v-html="trust.badgeHtml" />
    </div>
  </section>
</template>
