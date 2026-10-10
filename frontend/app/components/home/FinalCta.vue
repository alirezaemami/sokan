<template>
  <section class="relative overflow-hidden border-t border-line px-4 py-20 text-center sm:px-6 lg:px-8 lg:py-24">
    <ChartBackground :density="10" />
    <div v-reveal class="relative mx-auto max-w-3xl">
      <h2 class="font-display text-4xl leading-tight text-ink sm:text-5xl">
        {{ $t('home.final.title1') }} <span class="chart-em">{{ $t('home.final.title2') }}</span>
      </h2>
      <p class="mt-5 text-lg text-muted">{{ $t('home.final.subtitle') }}</p>
      <div class="mt-9 flex flex-col justify-center gap-3 sm:flex-row">
        <AppButton to="/get-quote" variant="accent" size="lg" icon-end="arrow-right">{{ $t('nav.getQuoteFree') }}</AppButton>
        <AppButton to="/register/forwarder" variant="secondary" size="lg">{{ $t('home.final.forwarder') }}</AppButton>
      </div>
    </div>
  </section>
</template>
