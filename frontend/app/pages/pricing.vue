<script setup lang="ts">
const api = useSokan()
const { t } = useI18n()
const fmt = useFormat()
const { data: plans } = await useAsyncData('plans', () => api.plans())

usePageSeo({ title: t('pricing.seoTitle'), description: t('pricing.seoDescription') })
useBreadcrumbs([{ name: t('nav.home'), item: '/' }, { name: t('nav.pricing'), item: '/pricing' }])

// Simple monthly cost estimator so a forwarder can find their plan.
const unlocks = ref(30)
const quotes = ref(20)
const costs = computed(() =>
  (plans.value ?? []).map((p) => {
    const paidViews = Math.max(unlocks.value - p.free_views_per_month, 0)
    const paidQuotes = Math.max(quotes.value - p.free_quotes_per_month, 0)
    return { name: p.name, currency: p.currency, total: p.monthly_fee + paidViews * p.view_fee + paidQuotes * p.quote_fee }
  }),
)
const cheapest = computed(() => costs.value.reduce((a, b) => (b.total < a.total ? b : a), costs.value[0]!))
</script>

<template>
  <div>
    <PageHero :eyebrow="$t('nav.pricing')" :title="$t('pricing.heroTitle')" :subtitle="$t('pricing.heroSubtitle')" />

    <section class="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div class="mx-auto mb-14 max-w-3xl rounded-3xl bg-success/10 p-6 text-center ring-1 ring-success/25">
        <p class="font-bold text-success">{{ $t('pricing.shippersFree') }}</p>
        <p class="mt-1 text-sm text-ink-soft">{{ $t('pricing.shippersFreeText') }}</p>
      </div>

      <div class="grid gap-6 lg:grid-cols-3">
        <div v-for="(p, i) in plans" :key="p.name" v-reveal="i * 90"><PlanCard :plan="p" /></div>
      </div>
    </section>

    <section v-if="costs.length" class="mx-auto max-w-4xl px-4 pb-24 sm:px-6 lg:px-8">
      <div class="card p-7 sm:p-10">
        <h2 class="font-display text-3xl text-ink">{{ $t('pricing.calcTitle') }}</h2>
        <p class="mt-2 text-muted">{{ $t('pricing.calcText') }}</p>
        <div class="mt-8 grid gap-8 sm:grid-cols-2">
          <label class="block">
            <span class="flex justify-between text-sm font-semibold"><span>{{ $t('pricing.calcUnlocks') }}</span><span class="text-sea">{{ fmt.number(unlocks) }}</span></span>
            <input v-model.number="unlocks" type="range" min="0" max="400" step="5" class="mt-3 w-full accent-sea" />
          </label>
          <label class="block">
            <span class="flex justify-between text-sm font-semibold"><span>{{ $t('pricing.calcQuotes') }}</span><span class="text-sea">{{ fmt.number(quotes) }}</span></span>
            <input v-model.number="quotes" type="range" min="0" max="400" step="5" class="mt-3 w-full accent-sea" />
          </label>
        </div>
        <div class="mt-8 grid gap-3 sm:grid-cols-3">
          <div
            v-for="c in costs"
            :key="c.name"
            class="rounded-2xl p-5 transition-all duration-300"
            :class="c.name === cheapest?.name ? 'bg-night-900 text-white' : 'bg-sunken'"
          >
            <p class="text-sm font-semibold opacity-80">{{ c.name }}</p>
            <p class="font-display mt-1 text-3xl tabular-nums">{{ fmt.money(c.total, c.currency) }}</p>
            <p v-if="c.name === cheapest?.name" class="mt-1 text-xs font-bold">{{ $t('pricing.bestForYou') }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="px-4 pb-24 sm:px-6 lg:px-8">
      <SectionHeading :title="$t('faq.forwarders.title')" />
      <div class="mt-12"><FaqSection group="faq.forwarders" :count="5" /></div>
    </section>
  </div>
</template>
