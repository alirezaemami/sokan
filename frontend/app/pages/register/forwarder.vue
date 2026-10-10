<script setup lang="ts">
definePageMeta({ layout: 'auth' })
const { t } = useI18n()
usePageSeo({ title: t('auth.fwdTitle'), description: t('auth.fwdSubtitle') })

const api = useSokan()
const { setMe, isLoggedIn, isForwarder } = useAuth()
const localePath = useLocalePath()
const errorMessage = useErrorMessage()
const { modes, load } = useModes()
onMounted(load)

// Already a forwarder? Straight to the portal.
watchEffect(() => {
  if (isForwarder.value) navigateTo(localePath('/partner'))
})

const step = ref(0)
const form = reactive({
  company_name: '',
  country: null as string | null,
  city: '',
  website: '',
  license_number: '',
  modes: [] as string[],
  full_name: '',
  email: '',
  phone: '',
  password: '',
})
const loading = ref(false)
const error = ref('')

function toggle(m: string) {
  const i = form.modes.indexOf(m)
  i >= 0 ? form.modes.splice(i, 1) : form.modes.push(m)
}

function next() {
  error.value = ''
  if (!form.company_name.trim() || !form.country || !form.modes.length) {
    error.value = t('auth.fwdStep1Error')
    return
  }
  step.value = 1
}

async function submit() {
  if (form.password.length < 8) {
    error.value = t('auth.passwordShort')
    return
  }
  loading.value = true
  error.value = ''
  try {
    setMe(await api.registerForwarder({ ...form }))
    await navigateTo(localePath('/partner'))
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <p class="text-sm font-bold text-sea">{{ $t('wizard.stepOf', { n: step + 1, total: 2 }) }}</p>
    <h1 class="mt-1 text-3xl font-bold">{{ $t('auth.fwdTitle') }}</h1>
    <p class="mt-2 text-muted">{{ $t('auth.fwdSubtitle') }}</p>

    <div v-if="isLoggedIn && !isForwarder" class="mt-6 rounded-xl bg-warning/12 p-4 text-sm">{{ $t('auth.fwdLoggedIn') }}</div>

    <AnimatePresence mode="wait">
      <Motion v-if="step === 0" key="s0" as="form" class="mt-8 space-y-5" :initial="{ opacity: 0, x: 30 }" :animate="{ opacity: 1, x: 0 }" :exit="{ opacity: 0, x: -30 }" @submit.prevent="next">
        <FormField v-model="form.company_name" :label="$t('fields.companyName')" icon="building" required autocomplete="organization" />
        <div class="grid gap-4 sm:grid-cols-2">
          <CountrySelect v-model="form.country" :label="$t('fields.country')" required />
          <FormField v-model="form.city" :label="$t('fields.city')" />
        </div>
        <div>
          <p class="mb-2 text-sm font-semibold text-ink-soft">{{ $t('auth.fwdModes') }} <span class="text-buoy">*</span></p>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="m in modes"
              :key="m.name"
              type="button"
              class="flex items-center gap-2 rounded-xl border-2 px-3 py-2.5 text-start text-sm font-semibold transition-all"
              :class="form.modes.includes(m.name) ? 'border-sea bg-sea/8 text-sea' : 'border-line hover:border-sea/30'"
              @click="toggle(m.name)"
            >
              <AppIcon :name="m.icon" :size="17" /> {{ $t(`modes.${m.code}.name`) }}
            </button>
          </div>
        </div>
        <div class="grid gap-4 sm:grid-cols-2">
          <FormField v-model="form.website" type="url" :label="$t('fields.website')" :hint="$t('common.optional')" dir="ltr" />
          <FormField v-model="form.license_number" :label="$t('fields.license')" :hint="$t('common.optional')" />
        </div>
        <Transition name="fade"><p v-if="error" class="rounded-xl bg-danger/10 p-3 text-sm text-danger">{{ error }}</p></Transition>
        <AppButton type="submit" variant="primary" size="lg" block icon-end="arrow-right">{{ $t('common.continue') }}</AppButton>
      </Motion>

      <Motion v-else key="s1" as="form" class="mt-8 space-y-5" :initial="{ opacity: 0, x: 30 }" :animate="{ opacity: 1, x: 0 }" :exit="{ opacity: 0, x: -30 }" @submit.prevent="submit">
        <FormField v-model="form.full_name" :label="$t('fields.yourName')" icon="user" required autocomplete="name" />
        <FormField v-model="form.email" type="email" :label="$t('fields.workEmail')" icon="mail" required autocomplete="email" dir="ltr" />
        <FormField v-model="form.phone" type="tel" :label="$t('fields.phone')" icon="phone" required autocomplete="tel" dir="ltr" />
        <FormField v-model="form.password" type="password" :label="$t('fields.password')" icon="lock" required autocomplete="new-password" :hint="$t('auth.passwordHint')" />
        <Transition name="fade"><p v-if="error" class="rounded-xl bg-danger/10 p-3 text-sm text-danger">{{ error }}</p></Transition>
        <div class="flex gap-3">
          <AppButton variant="secondary" size="lg" icon="arrow-left" @click="step = 0">{{ $t('common.back') }}</AppButton>
          <AppButton type="submit" variant="accent" size="lg" class="flex-1" :loading="loading" icon-end="arrow-right">{{ $t('auth.fwdSubmit') }}</AppButton>
        </div>
        <p class="text-center text-xs text-faint">{{ $t('auth.fwdReview') }}</p>
      </Motion>
    </AnimatePresence>

    <p class="mt-8 text-center text-sm text-muted">
      {{ $t('auth.haveAccount') }} <NuxtLinkLocale to="/login" class="font-semibold text-sea">{{ $t('auth.login') }}</NuxtLinkLocale>
    </p>
  </div>
</template>
