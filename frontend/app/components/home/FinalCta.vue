<template>
  <section class="mx-auto max-w-7xl px-4 py-24 text-center sm:px-6 lg:px-8">
    <div v-reveal class="relative mx-auto max-w-3xl">
      <div class="absolute inset-x-10 -top-10 h-40 rounded-full bg-brand/20 blur-3xl" />
      <h2 class="relative text-4xl leading-tight font-extrabold sm:text-5xl">
        {{ $t('home.final.title1') }} <span class="text-gradient">{{ $t('home.final.title2') }}</span>
      </h2>
      <p class="relative mt-5 text-lg text-muted">{{ $t('home.final.subtitle') }}</p>
      <div class="relative mt-9 flex flex-col justify-center gap-3 sm:flex-row">
        <AppButton to="/get-quote" variant="accent" size="lg" icon-end="arrow-right">{{ $t('nav.getQuoteFree') }}</AppButton>
        <AppButton to="/register/forwarder" variant="secondary" size="lg">{{ $t('home.final.forwarder') }}</AppButton>
      </div>
    </div>
  </section>
</template>
