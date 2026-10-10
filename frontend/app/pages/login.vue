<script setup lang="ts">
definePageMeta({ layout: 'auth', middleware: 'guest' })
const { t } = useI18n()
usePageSeo({ title: t('auth.loginTitle'), noIndex: true })

const route = useRoute()
const { login, homePath } = useAuth()
const errorMessage = useErrorMessage()
const form = reactive({ email: '', password: '' })
const loading = ref(false)
const error = ref('')

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await login(form.email, form.password)
    const redirect = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/') ? route.query.redirect : homePath.value
    await navigateTo(redirect)
  } catch (e) {
    error.value = errorMessage(e, t('auth.badCredentials'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="text-3xl font-extrabold">{{ $t('auth.loginTitle') }}</h1>
    <p class="mt-2 text-muted">{{ $t('auth.loginSubtitle') }}</p>
    <form class="mt-8 space-y-5" @submit.prevent="submit">
      <FormField v-model="form.email" type="email" :label="$t('fields.email')" icon="mail" required autocomplete="email" dir="ltr" />
      <FormField v-model="form.password" type="password" :label="$t('fields.password')" icon="lock" required autocomplete="current-password" />
      <div class="flex justify-end">
        <NuxtLinkLocale to="/forgot-password" class="text-sm font-semibold text-brand">{{ $t('auth.forgot') }}</NuxtLinkLocale>
      </div>
      <Transition name="fade"><p v-if="error" class="rounded-xl bg-danger/10 p-3 text-sm text-danger">{{ error }}</p></Transition>
      <AppButton type="submit" variant="primary" size="lg" block :loading="loading" icon-end="arrow-right">{{ $t('auth.login') }}</AppButton>
    </form>
    <div class="mt-8 grid gap-3 sm:grid-cols-2">
      <NuxtLinkLocale to="/register" class="card flex items-center gap-3 p-4 transition-colors hover:border-brand/40">
        <AppIcon name="package" class="text-brand" />
        <span class="text-sm"><span class="block font-bold">{{ $t('auth.newShipper') }}</span><span class="text-muted">{{ $t('auth.createFree') }}</span></span>
      </NuxtLinkLocale>
      <NuxtLinkLocale to="/register/forwarder" class="card flex items-center gap-3 p-4 transition-colors hover:border-brand/40">
        <AppIcon name="building" class="text-coral" />
        <span class="text-sm"><span class="block font-bold">{{ $t('auth.newForwarder') }}</span><span class="text-muted">{{ $t('auth.joinNetwork') }}</span></span>
      </NuxtLinkLocale>
    </div>
  </div>
</template>
