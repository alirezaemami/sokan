<script setup lang="ts">
/** Confirm the email address after sign-up (or when an unconfirmed account signs in). */
definePageMeta({ layout: 'auth', middleware: 'auth', allowUnverified: true })
const { t } = useI18n()
usePageSeo({ title: t('verify.title'), noIndex: true })

const route = useRoute()
const { me, isForwarder, homePath } = useAuth()

const next = computed(() => {
  const r = route.query.redirect
  return typeof r === 'string' && r.startsWith('/') && !r.includes('verify-email') ? r : homePath.value
})

// Already confirmed (another tab, or a manager vouched for it): carry on.
if (me.value?.email_verified) await navigateTo(next.value, { replace: true })

async function done() {
  await navigateTo(next.value, { replace: true })
}
</script>

<template>
  <div>
    <span class="grid size-14 place-items-center rounded-2xl bg-sea/10 text-sea"><AppIcon name="mail" :size="26" /></span>
    <h1 class="font-display mt-6 text-4xl text-ink">{{ $t('verify.title') }}</h1>
    <p class="mt-2 text-muted">{{ isForwarder ? $t('verify.whyForwarder') : $t('verify.whyShipper') }}</p>
    <div class="mt-8">
      <EmailCodeForm @verified="done" />
    </div>
  </div>
</template>
