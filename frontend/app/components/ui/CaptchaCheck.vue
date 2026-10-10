<script setup lang="ts">
/**
 * "Not a robot" check for sign-in, sign-up and password reset.
 *
 * Starts solving Sokan's proof-of-work challenge as soon as the form appears,
 * so by the time the person submits there's usually nothing to wait for. Each
 * solution works once: `getToken()` hands it over and starts the next one, so a
 * failed attempt (wrong password) can be retried straight away.
 */
const api = useSokan()

// The server accepts a solution for 10 minutes; re-solve a little before that.
const MAX_AGE = 8 * 60 * 1000

const state = ref<'working' | 'done' | 'error'>('working')
let pending: Promise<string> | null = null
let solvedAt = 0
let controller: AbortController | null = null

function start() {
  controller?.abort()
  const ctrl = new AbortController()
  controller = ctrl
  state.value = 'working'
  const job = (async () => {
    const challenge = await api.captchaChallenge()
    const token = await solveCaptcha(challenge, ctrl.signal)
    solvedAt = Date.now()
    if (controller === ctrl) state.value = 'done'
    return token
  })()
  job.catch((e) => {
    if ((e as DOMException)?.name !== 'AbortError' && controller === ctrl) state.value = 'error'
  })
  pending = job
}

/** A fresh, unused solution (waits for the current solve if it's still running). */
async function getToken(): Promise<string> {
  if (!pending || state.value === 'error' || (state.value === 'done' && Date.now() - solvedAt > MAX_AGE)) start()
  const job = pending!
  pending = null
  try {
    return await job
  } finally {
    start()
  }
}

onMounted(start)
onBeforeUnmount(() => controller?.abort())

defineExpose({ getToken })
</script>

<template>
  <div class="flex items-center gap-3 rounded-xl border border-line bg-sunken/60 px-4 py-3 text-sm" role="status" aria-live="polite">
    <span class="grid size-6 shrink-0 place-items-center rounded-md border" :class="state === 'done' ? 'border-success bg-success text-white' : state === 'error' ? 'border-danger text-danger' : 'border-line-strong bg-surface'">
      <AppIcon v-if="state === 'done'" name="check" :size="15" :stroke-width="3" />
      <AppIcon v-else-if="state === 'error'" name="alert" :size="14" />
      <span v-else class="size-3.5 animate-spin rounded-full border-2 border-sea/30 border-t-sea" />
    </span>
    <span class="min-w-0 flex-1">
      <span class="block font-semibold text-ink">{{ state === 'done' ? $t('captcha.done') : state === 'error' ? $t('captcha.error') : $t('captcha.working') }}</span>
      <span class="block text-xs text-faint">{{ $t('captcha.hint') }}</span>
    </span>
    <button v-if="state === 'error'" type="button" class="text-sm font-semibold text-sea" @click="start">{{ $t('common.retry') }}</button>
  </div>
</template>
