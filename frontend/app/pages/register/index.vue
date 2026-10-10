<script setup lang="ts">
definePageMeta({ layout: 'auth', middleware: 'guest' })
const { t } = useI18n()
usePageSeo({ title: t('auth.registerTitle'), description: t('auth.registerSubtitle') })

const api = useSokan()
const { setMe } = useAuth()
const localePath = useLocalePath()
const errorMessage = useErrorMessage()

const form = reactive({ full_name: '', email: '', phone: '', company_name: '', password: '', customer_type: 'Business' })
const loading = ref(false)
const error = ref('')

async function submit() {
  if (form.password.length < 8) {
    error.value = t('auth.passwordShort')
    return
  }
  loading.value = true
  error.value = ''
  try {
    setMe(await api.registerCustomer({ ...form }))
    await navigateTo(localePath('/get-quote'))
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="text-3xl font-extrabold">{{ $t('auth.registerTitle') }}</h1>
    <p class="mt-2 text-muted">{{ $t('auth.registerSubtitle') }}</p>
    <form class="mt-8 space-y-5" @submit.prevent="submit">
      <div class="grid grid-cols-2 rounded-xl bg-sunken p-1 text-sm font-semibold">
        <button v-for="ct in ['Business', 'Individual']" :key="ct" type="button" class="rounded-lg py-2 transition-all" :class="form.customer_type === ct ? 'bg-surface shadow-sm' : 'text-muted'" @click="form.customer_type = ct">
          {{ $t(`auth.type.${ct}`) }}
        </button>
      </div>
      <FormField v-model="form.full_name" :label="$t('fields.fullName')" icon="user" required autocomplete="name" />
      <FormField v-if="form.customer_type === 'Business'" v-model="form.company_name" :label="$t('fields.company')" icon="building" autocomplete="organization" />
      <FormField v-model="form.email" type="email" :label="$t('fields.email')" icon="mail" required autocomplete="email" dir="ltr" />
      <FormField v-model="form.phone" type="tel" :label="$t('fields.phone')" icon="phone" autocomplete="tel" dir="ltr" />
      <FormField v-model="form.password" type="password" :label="$t('fields.password')" icon="lock" required autocomplete="new-password" :hint="$t('auth.passwordHint')" />
      <Transition name="fade"><p v-if="error" class="rounded-xl bg-danger/10 p-3 text-sm text-danger">{{ error }}</p></Transition>
      <AppButton type="submit" variant="primary" size="lg" block :loading="loading" icon-end="arrow-right">{{ $t('auth.createAccount') }}</AppButton>
      <p class="text-center text-xs text-faint">
        {{ $t('auth.agree') }} <NuxtLinkLocale to="/terms" class="underline">{{ $t('footer.terms') }}</NuxtLinkLocale> · <NuxtLinkLocale to="/privacy" class="underline">{{ $t('footer.privacy') }}</NuxtLinkLocale>
      </p>
    </form>
    <p class="mt-8 text-center text-sm text-muted">
      {{ $t('auth.haveAccount') }} <NuxtLinkLocale to="/login" class="font-semibold text-brand">{{ $t('auth.login') }}</NuxtLinkLocale>
      · <NuxtLinkLocale to="/register/forwarder" class="font-semibold text-brand">{{ $t('auth.imForwarder') }}</NuxtLinkLocale>
    </p>
  </div>
</template>
