<script setup lang="ts">
const api = useSokan()
const { t } = useI18n()
const { data: plans } = await useAsyncData('plans', () => api.plans())

usePageSeo({ title: t('forForwarders.seoTitle'), description: t('forForwarders.seoDescription') })
useBreadcrumbs([{ name: t('nav.home'), item: '/' }, { name: t('nav.forForwarders'), item: '/for-forwarders' }])

const benefits = [
  { icon: 'inbox', key: 'b1' },
  { icon: 'target', key: 'b2' },
  { icon: 'eye', key: 'b3' },
  { icon: 'wallet', key: 'b4' },
  { icon: 'star', key: 'b5' },
  { icon: 'chart', key: 'b6' },
]
</script>

<template>
  <div>
    <PageHero :eyebrow="$t('forForwarders.eyebrow')" :title="$t('forForwarders.title')" :subtitle="$t('forForwarders.subtitle')">
      <div class="flex flex-col justify-center gap-3 sm:flex-row">
        <AppButton to="/register/forwarder" variant="accent" size="lg" icon-end="arrow-right">{{ $t('home.forwarders.cta') }}</AppButton>
        <AppButton to="/pricing" variant="glass" size="lg">{{ $t('nav.pricing') }}</AppButton>
      </div>
    </PageHero>

    <section class="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="(b, i) in benefits" :key="b.key" v-reveal="(i % 3) * 80" class="card p-7">
          <span class="grid size-12 place-items-center rounded-2xl bg-brand/10 text-brand"><AppIcon :name="b.icon" :size="24" /></span>
          <h3 class="mt-5 text-lg font-bold">{{ $t(`forForwarders.${b.key}.title`) }}</h3>
          <p class="mt-2 text-sm leading-relaxed text-muted">{{ $t(`forForwarders.${b.key}.text`) }}</p>
        </div>
      </div>
    </section>

    <HowItWorks initial="forwarders" />

    <!-- The billing model, explained plainly -->
    <section class="mx-auto max-w-5xl px-4 pb-20 sm:px-6 lg:px-8">
      <div class="card overflow-hidden p-0">
        <div class="grid md:grid-cols-3">
          <div v-for="(k, i) in ['free', 'unlock', 'quote']" :key="k" v-reveal="i * 90" class="border-line p-7 md:border-e last:border-e-0" :class="i < 2 && 'border-b md:border-b-0'">
            <span class="text-sm font-bold text-brand">0{{ i + 1 }}</span>
            <h3 class="mt-2 text-lg font-bold">{{ $t(`forForwarders.billing.${k}.title`) }}</h3>
            <p class="mt-2 text-sm leading-relaxed text-muted">{{ $t(`forForwarders.billing.${k}.text`) }}</p>
          </div>
        </div>
      </div>
    </section>

    <section v-if="plans?.length" class="mx-auto max-w-7xl px-4 pb-24 sm:px-6 lg:px-8">
      <SectionHeading :eyebrow="$t('nav.pricing')" :title="$t('pricing.title')" :subtitle="$t('pricing.subtitle')" />
      <div class="mt-14 grid gap-6 lg:grid-cols-3">
        <div v-for="(p, i) in plans" :key="p.name" v-reveal="i * 90"><PlanCard :plan="p" /></div>
      </div>
    </section>

    <section class="px-4 pb-24 sm:px-6 lg:px-8">
      <SectionHeading :title="$t('faq.forwarders.title')" />
      <div class="mt-12"><FaqSection group="faq.forwarders" :count="5" /></div>
    </section>
  </div>
</template>
