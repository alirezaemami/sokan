<script setup lang="ts">
const route = useRoute()
const api = useSokan()
const fmt = useFormat()
const { t } = useI18n()
const { siteUrl } = useRuntimeConfig().public

const { data: f, error } = await useAsyncData(`forwarder-${route.params.slug}`, () => api.forwarder(String(route.params.slug)))
if (error.value || !f.value) {
  throw createError({ statusCode: 404, statusMessage: 'Forwarder not found', fatal: true })
}

const location = computed(() => fmt.place(f.value!))

usePageSeo(() => ({
  title: t('profile.seoTitle', { name: f.value!.company_name, place: location.value }),
  description: f.value!.meta_description || f.value!.tagline || t('profile.seoFallback', { name: f.value!.company_name }),
  image: f.value!.cover_image || f.value!.logo,
  type: 'profile',
}))
useBreadcrumbs([
  { name: t('nav.home'), item: '/' },
  { name: t('nav.forwarders'), item: '/forwarders' },
  { name: f.value.company_name, item: `/forwarders/${f.value.slug}` },
])
useSchemaOrg([
  defineOrganization({
    name: f.value.company_name,
    url: `${siteUrl}/forwarders/${f.value.slug}`,
    logo: f.value.logo || undefined,
    description: f.value.tagline || undefined,
    foundingDate: f.value.established_year ? String(f.value.established_year) : undefined,
    address: { addressCountry: f.value.country_code || undefined, addressLocality: f.value.city || undefined },
    ...(f.value.review_count
      ? { aggregateRating: { ratingValue: f.value.rating, reviewCount: f.value.review_count, bestRating: 5 } }
      : {}),
  } as Parameters<typeof defineOrganization>[0]),
])
</script>

<template>
  <div v-if="f">
    <section class="relative overflow-hidden bg-night-950 pt-[72px] text-white">
      <img v-if="f.cover_image" :src="f.cover_image" alt="" class="absolute inset-0 size-full object-cover opacity-25" />
      <ChartBackground tone="night" />
      <div class="relative mx-auto max-w-6xl px-4 pt-10 pb-16 sm:px-6 lg:px-8">
        <NuxtLinkLocale to="/forwarders" class="inline-flex items-center gap-1.5 text-sm text-white/60 hover:text-white">
          <AppIcon name="arrow-left" :size="16" flip /> {{ $t('profile.back') }}
        </NuxtLinkLocale>
        <div class="mt-6 flex flex-col gap-6 sm:flex-row sm:items-end">
          <CompanyAvatar :name="f.company_name" :logo="f.logo" size="xl" />
          <div class="min-w-0 flex-1">
            <h1 class="font-display flex flex-wrap items-center gap-2 text-4xl sm:text-5xl">
              {{ f.company_name }}
              <span v-if="f.is_verified" class="inline-flex items-center gap-1 rounded-full bg-tide/15 px-2.5 py-1 text-xs font-bold text-tide">
                <AppIcon name="badge-check" :size="15" /> {{ $t('common.verified') }}
              </span>
            </h1>
            <p v-if="f.tagline" class="mt-2 text-lg text-white/70">{{ f.tagline }}</p>
            <div class="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-white/65">
              <span>{{ fmt.flag(f.country_code) }} {{ location }}</span>
              <span v-if="f.established_year">{{ $t('profile.since', { year: f.established_year }) }}</span>
              <span v-if="f.review_count" class="flex items-center gap-1.5"><RatingStars :model-value="f.rating" :size="14" /> {{ fmt.number(f.rating, 1) }} ({{ fmt.number(f.review_count) }})</span>
            </div>
          </div>
          <AppButton to="/get-quote" variant="accent" size="lg" icon-end="arrow-right">{{ $t('profile.requestQuote') }}</AppButton>
        </div>
      </div>
    </section>

    <div class="mx-auto grid max-w-6xl gap-6 px-4 py-12 sm:px-6 lg:grid-cols-[1fr_340px] lg:px-8">
      <div class="space-y-6">
        <section v-if="f.about" class="card p-7">
          <h2 class="text-lg font-bold">{{ $t('profile.about') }}</h2>
          <div class="prose-sokan mt-4 leading-relaxed text-ink-soft" v-html="f.about" />
        </section>

        <section class="card p-7">
          <h2 class="text-lg font-bold">{{ $t('profile.services') }}</h2>
          <div class="mt-5 grid gap-3 sm:grid-cols-2">
            <div v-for="m in f.modes" :key="m.name" class="flex items-center gap-3 rounded-xl bg-sunken p-3.5">
              <span class="grid size-10 place-items-center rounded-xl bg-sea/10 text-sea"><AppIcon :name="m.icon" :size="20" /></span>
              <span class="font-semibold">{{ $t(`modes.${m.code}.name`) }}</span>
            </div>
          </div>
        </section>

        <section class="card p-7">
          <h2 class="text-lg font-bold">{{ $t('profile.reviews') }}</h2>
          <div v-if="f.reviews.length" class="mt-5 divide-y divide-line">
            <article v-for="(r, i) in f.reviews" :key="i" class="py-5 first:pt-0 last:pb-0">
              <div class="flex items-center justify-between gap-3">
                <p class="font-semibold">{{ r.customer_name }}</p>
                <RatingStars :model-value="r.rating" :size="14" />
              </div>
              <p v-if="r.comment" class="mt-2 text-sm leading-relaxed text-ink-soft">{{ r.comment }}</p>
              <p class="mt-2 text-xs text-faint">{{ fmt.date(r.creation) }}</p>
            </article>
          </div>
          <p v-else class="mt-3 text-sm text-muted">{{ $t('profile.noReviews') }}</p>
        </section>
      </div>

      <aside class="space-y-6">
        <section class="card grid grid-cols-2 gap-px overflow-hidden bg-line p-0">
          <div class="bg-surface p-5">
            <p class="text-2xl font-bold">{{ fmt.number(f.stats.quotes_sent) }}</p>
            <p class="text-xs text-muted">{{ $t('profile.quotesSent') }}</p>
          </div>
          <div class="bg-surface p-5">
            <p class="text-2xl font-bold">{{ f.stats.win_rate != null ? `${fmt.number(f.stats.win_rate)}%` : '—' }}</p>
            <p class="text-xs text-muted">{{ $t('profile.winRate') }}</p>
          </div>
        </section>

        <section v-if="f.coverage.length" class="card p-6">
          <h2 class="font-bold">{{ $t('profile.coverage') }}</h2>
          <div class="mt-4 flex flex-wrap gap-2">
            <span v-for="c in f.coverage" :key="c.name" class="rounded-lg bg-sunken px-2.5 py-1 text-sm">{{ fmt.flag(c.code) }} {{ fmt.country(c.code, c.name) }}</span>
          </div>
        </section>
        <section v-else class="card p-6">
          <h2 class="font-bold">{{ $t('profile.coverage') }}</h2>
          <p class="mt-2 flex items-center gap-2 text-sm text-muted"><AppIcon name="earth" :size="18" /> {{ $t('profile.worldwide') }}</p>
        </section>

        <section v-if="f.certifications.length" class="card p-6">
          <h2 class="font-bold">{{ $t('profile.certifications') }}</h2>
          <ul class="mt-4 space-y-2">
            <li v-for="c in f.certifications" :key="c" class="flex items-center gap-2 text-sm"><AppIcon name="award" :size="16" class="text-sea" /> {{ c }}</li>
          </ul>
        </section>

        <section class="rounded-2xl bg-night-900 p-6 text-white">
          <h2 class="font-bold">{{ $t('profile.ctaTitle') }}</h2>
          <p class="mt-2 text-sm text-white/80">{{ $t('profile.ctaText') }}</p>
          <AppButton to="/get-quote" variant="night" class="mt-5" block icon-end="arrow-right">{{ $t('nav.getQuoteFree') }}</AppButton>
        </section>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.prose-sokan :deep(p) { margin-bottom: 0.9em; }
.prose-sokan :deep(ul) { list-style: disc; padding-inline-start: 1.25rem; margin-bottom: 0.9em; }
.prose-sokan :deep(a) { color: var(--sea); text-decoration: underline; }
</style>
