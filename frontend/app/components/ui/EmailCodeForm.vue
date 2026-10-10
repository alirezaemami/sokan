<script setup lang="ts">
import type { Me } from '~/types/sokan'

/**
 * Enter the 6-digit code we emailed. Used by /verify-email and inline at the
 * end of the request wizard. Asks the server for a code on mount (it won't
 * resend while a recent one is still valid), submits by itself once six digits
 * are in, and accepts Persian digits from phone keyboards.
 */
const emit = defineEmits<{ verified: [me: Me] }>()

const api = useSokan()
const toast = useToast()
const { t } = useI18n()
const { me, setMe, logout } = useAuth()
const errorMessage = useErrorMessage()

const code = ref('')
const error = ref('')
const loading = ref(false)
const resending = ref(false)
const resendIn = ref(0)
const input = ref<HTMLInputElement | null>(null)
let timer: ReturnType<typeof setInterval> | undefined

const FA_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩'

function countdown(seconds: number) {
  resendIn.value = Math.max(0, Math.round(seconds))
  clearInterval(timer)
  timer = setInterval(() => {
    resendIn.value = Math.max(0, resendIn.value - 1)
    if (!resendIn.value) clearInterval(timer)
  }, 1000)
}

async function finish(data: Me) {
  setMe(data)
  emit('verified', data)
}

async function send(force: boolean) {
  const res = await api.sendVerificationCode(force)
  if (res.verified) {
    await finish(await api.me())
    return
  }
  countdown(res.resend_in ?? 0)
  if (force && res.sent) toast.success(t('verify.resent'))
}

async function resend() {
  resending.value = true
  error.value = ''
  try {
    await send(true)
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    resending.value = false
  }
}

function onInput(e: Event) {
  const raw = (e.target as HTMLInputElement).value
  code.value = raw
    .replace(/[۰-۹]/g, (d) => String(FA_DIGITS.indexOf(d)))
    .replace(/[٠-٩]/g, (d) => String(AR_DIGITS.indexOf(d)))
    .replace(/\D/g, '')
    .slice(0, 6)
  ;(e.target as HTMLInputElement).value = code.value
  if (code.value.length === 6) submit()
}

async function submit() {
  if (code.value.length !== 6 || loading.value) return
  loading.value = true
  error.value = ''
  try {
    await finish(await api.verifyEmail(code.value))
  } catch (e) {
    error.value = errorMessage(e)
    code.value = ''
    input.value?.focus()
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  input.value?.focus()
  try {
    await send(false)
  } catch (e) {
    error.value = errorMessage(e)
  }
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <form class="space-y-5" @submit.prevent="submit">
    <p class="text-muted">
      {{ $t('verify.sentTo') }} <bdi class="font-semibold break-all text-ink" dir="ltr">{{ me?.user }}</bdi>
    </p>
    <label class="block">
      <span class="mb-2 block text-sm font-semibold">{{ $t('verify.codeLabel') }}</span>
      <input
        ref="input"
        :value="code"
        type="text"
        inputmode="numeric"
        autocomplete="one-time-code"
        maxlength="6"
        dir="ltr"
        placeholder="••••••"
        class="block w-full rounded-2xl border border-line-strong bg-surface px-4 py-4 text-center font-mono text-3xl font-bold tracking-[0.5em] text-ink outline-none transition focus:border-sea focus:ring-4 focus:ring-sea/15 placeholder:text-faint"
        :aria-invalid="Boolean(error)"
        @input="onInput"
      />
    </label>
    <Transition name="fade"><p v-if="error" class="rounded-xl bg-danger/10 p-3 text-sm text-danger">{{ error }}</p></Transition>
    <AppButton type="submit" variant="primary" size="lg" block :loading="loading" :disabled="code.length !== 6" icon-end="arrow-right">{{ $t('verify.confirm') }}</AppButton>
    <div class="flex flex-wrap items-center justify-between gap-3 text-sm">
      <button type="button" class="font-semibold text-sea disabled:text-faint" :disabled="resendIn > 0 || resending" @click="resend">
        {{ resendIn > 0 ? $t('verify.resendIn', { s: resendIn }) : $t('verify.resend') }}
      </button>
      <button type="button" class="text-muted hover:text-ink" @click="logout">{{ $t('verify.wrongEmail') }}</button>
    </div>
    <p class="text-xs text-faint">{{ $t('verify.spam') }}</p>
  </form>
</template>
