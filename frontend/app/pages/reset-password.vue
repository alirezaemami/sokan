<script setup lang="ts">
/** Landing page for the emailed reset link: choose a new password, then go straight in. */
definePageMeta({ layout: 'auth' })
const { t } = useI18n()
usePageSeo({ title: t('auth.resetTitle'), noIndex: true })
const route = useRoute()
const api = useSokan()
const { setMe, homePath } = useAuth()
const errorMessage = useErrorMessage()

const key = computed(() => String(route.query.key || ''))
const password = ref('')
const confirm = ref('')
const show = ref(false)
const loading = ref(false)
const error = ref('')

const mismatch = computed(() => confirm.value.length > 0 && confirm.value !== password.value)
const ready = computed(() => password.value.length >= 8 && password.value === confirm.value)

async function submit() {
  if (!ready.value) return
  loading.value = true
  error.value = ''
  try {
    setMe(await api.resetPassword(key.value, password.value))
    await navigateTo(homePath.value)
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="font-display text-4xl text-ink">{{ $t('auth.resetTitle') }}</h1>
    <template v-if="key">
      <p class="mt-2 text-muted">{{ $t('auth.resetSubtitle') }}</p>
      <form class="mt-8 space-y-5" @submit.prevent="submit">
        <FormField
          v-model="password"
          :type="show ? 'text' : 'password'"
          :label="$t('auth.newPassword')"
          :hint="$t('auth.passwordHint')"
          icon="lock"
          required
          autocomplete="new-password"
          dir="ltr"
        />
        <FormField
          v-model="confirm"
          :type="show ? 'text' : 'password'"
          :label="$t('auth.confirmPassword')"
          :error="mismatch ? $t('auth.passwordMismatch') : null"
          icon="lock"
          required
          autocomplete="new-password"
          dir="ltr"
        />
        <label class="flex cursor-pointer items-center gap-2 text-sm text-muted">
          <input v-model="show" type="checkbox" class="size-4 accent-[var(--sea)]" /> {{ $t('auth.showPassword') }}
        </label>
        <p v-if="error" class="rounded-xl bg-danger/10 p-3 text-sm text-danger">
          {{ error }}
          <NuxtLinkLocale to="/forgot-password" class="mt-1 block font-semibold underline">{{ $t('auth.requestNewLink') }}</NuxtLinkLocale>
        </p>
        <AppButton type="submit" variant="primary" size="lg" block :loading="loading" :disabled="!ready">{{ $t('auth.savePassword') }}</AppButton>
      </form>
    </template>
    <div v-else class="mt-8 rounded-2xl bg-danger/10 p-5 text-sm text-danger">
      {{ $t('auth.resetMissing') }}
      <NuxtLinkLocale to="/forgot-password" class="mt-2 block font-semibold underline">{{ $t('auth.requestNewLink') }}</NuxtLinkLocale>
    </div>
    <p class="mt-8 text-center text-sm"><NuxtLinkLocale to="/login" class="font-semibold text-sea">{{ $t('auth.backToLogin') }}</NuxtLinkLocale></p>
  </div>
</template>
