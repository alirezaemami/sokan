<script setup lang="ts">
const api = useSokan()
const { t } = useI18n()
const toast = useToast()
const errorMessage = useErrorMessage()

usePageSeo({ title: t('contact.seoTitle'), description: t('contact.subtitle') })
useBreadcrumbs([{ name: t('nav.home'), item: '/' }, { name: t('nav.contact'), item: '/contact' }])

const form = reactive({ full_name: '', email: '', phone: '', company: '', audience: 'Shipper', subject: '', message: '' })
const sending = ref(false)
const sent = ref(false)

async function submit() {
  sending.value = true
  try {
    await api.contact({ ...form })
    sent.value = true
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div>
    <PageHero compact :eyebrow="$t('nav.contact')" :title="$t('contact.title')" :subtitle="$t('contact.subtitle')" />
    <section class="mx-auto grid max-w-6xl gap-8 px-4 py-16 sm:px-6 lg:grid-cols-[1fr_1.4fr] lg:px-8">
      <div class="space-y-4">
        <div v-for="(c, i) in [{ icon: 'mail', key: 'email' }, { icon: 'message', key: 'chat' }, { icon: 'clock', key: 'hours' }]" :key="c.key" v-reveal="i * 80" class="card flex gap-4 p-6">
          <span class="grid size-12 shrink-0 place-items-center rounded-2xl bg-brand/10 text-brand"><AppIcon :name="c.icon" :size="22" /></span>
          <div>
            <h3 class="font-bold">{{ $t(`contact.${c.key}.title`) }}</h3>
            <p class="mt-1 text-sm text-muted">{{ $t(`contact.${c.key}.text`) }}</p>
          </div>
        </div>
      </div>

      <div class="card p-6 sm:p-8">
        <Transition name="fade" mode="out-in">
          <div v-if="sent" class="py-10 text-center">
            <div class="mx-auto grid size-16 place-items-center rounded-full bg-success/15 text-success"><AppIcon name="check" :size="30" /></div>
            <h2 class="mt-5 text-2xl font-bold">{{ $t('contact.sentTitle') }}</h2>
            <p class="mt-2 text-muted">{{ $t('contact.sentText') }}</p>
          </div>
          <form v-else class="grid gap-5 sm:grid-cols-2" @submit.prevent="submit">
            <FormField v-model="form.full_name" :label="$t('fields.fullName')" required autocomplete="name" />
            <FormField v-model="form.email" :label="$t('fields.email')" type="email" required autocomplete="email" dir="ltr" />
            <FormField v-model="form.phone" :label="$t('fields.phone')" type="tel" autocomplete="tel" dir="ltr" />
            <FormField v-model="form.company" :label="$t('fields.company')" autocomplete="organization" />
            <FormField v-model="form.audience" as="select" :label="$t('contact.iAm')" class="sm:col-span-2">
              <template #options>
                <option v-for="a in ['Shipper', 'Forwarder', 'Partner', 'Other']" :key="a" :value="a">{{ $t(`contact.audience.${a}`) }}</option>
              </template>
            </FormField>
            <FormField v-model="form.subject" :label="$t('fields.subject')" class="sm:col-span-2" />
            <FormField v-model="form.message" as="textarea" :rows="5" :label="$t('fields.message')" required class="sm:col-span-2" />
            <AppButton type="submit" variant="primary" size="lg" :loading="sending" icon-end="send" class="sm:col-span-2">{{ $t('contact.send') }}</AppButton>
          </form>
        </Transition>
      </div>
    </section>
  </div>
</template>
