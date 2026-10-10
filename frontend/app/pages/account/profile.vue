<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'customer' })
const { t } = useI18n()
useHead({ title: t('portal.nav.profile') })
const api = useSokan()
const toast = useToast()
const errorMessage = useErrorMessage()
const { refresh } = useAuth()

const form = reactive({ full_name: '', phone: '', company_name: '', country: null as string | null, city: '', customer_type: 'Business', email: '' })
const loading = ref(true)
const saving = ref(false)

onMounted(async () => {
  Object.assign(form, await api.customer.profile())
  loading.value = false
})

async function save() {
  saving.value = true
  try {
    Object.assign(form, await api.customer.updateProfile({ ...form }))
    await refresh()
    toast.success(t('common.saved'))
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl">
    <PortalHeading :title="$t('portal.nav.profile')" />
    <div v-if="loading" class="skeleton h-96" />
    <form v-else class="card grid gap-5 p-6 sm:grid-cols-2" @submit.prevent="save">
      <FormField v-model="form.full_name" :label="$t('fields.fullName')" required />
      <div class="flex flex-col gap-1.5">
        <span class="text-sm font-semibold text-ink-soft">{{ $t('fields.email') }}</span>
        <span class="flex h-12 items-center rounded-xl bg-sunken px-4 text-muted" dir="ltr">{{ form.email }}</span>
      </div>
      <FormField v-model="form.phone" type="tel" :label="$t('fields.phone')" dir="ltr" />
      <FormField v-model="form.company_name" :label="$t('fields.company')" />
      <CountrySelect v-model="form.country" :label="$t('fields.country')" />
      <FormField v-model="form.city" :label="$t('fields.city')" />
      <AppButton type="submit" variant="primary" :loading="saving" class="sm:col-span-2 sm:justify-self-start">{{ $t('common.save') }}</AppButton>
    </form>
  </div>
</template>
