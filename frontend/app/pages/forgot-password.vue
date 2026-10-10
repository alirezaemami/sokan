<script setup lang="ts">
definePageMeta({ layout: 'auth', middleware: 'guest' })
const { t } = useI18n()
usePageSeo({ title: t('auth.forgotTitle'), noIndex: true })
const api = useSokan()
const errorMessage = useErrorMessage()
const email = ref('')
const loading = ref(false)
const sent = ref(false)
const error = ref('')

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await api.resetPassword(email.value.trim().toLowerCase())
    sent.value = true
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="text-3xl font-extrabold">{{ $t('auth.forgotTitle') }}</h1>
    <p class="mt-2 text-muted">{{ $t('auth.forgotSubtitle') }}</p>
    <div v-if="sent" class="mt-8 rounded-2xl bg-success/10 p-5 text-sm">
      <AppIcon name="mail" class="text-success" />
      <p class="mt-2">{{ $t('auth.forgotSent') }}</p>
    </div>
    <form v-else class="mt-8 space-y-5" @submit.prevent="submit">
      <FormField v-model="email" type="email" :label="$t('fields.email')" icon="mail" required autocomplete="email" dir="ltr" />
      <p v-if="error" class="rounded-xl bg-danger/10 p-3 text-sm text-danger">{{ error }}</p>
      <AppButton type="submit" variant="primary" size="lg" block :loading="loading">{{ $t('auth.sendLink') }}</AppButton>
    </form>
    <p class="mt-8 text-center text-sm"><NuxtLinkLocale to="/login" class="font-semibold text-brand">{{ $t('auth.backToLogin') }}</NuxtLinkLocale></p>
  </div>
</template>
