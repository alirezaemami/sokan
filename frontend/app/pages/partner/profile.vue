<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth', role: 'forwarder' })
const { t } = useI18n()
useHead({ title: t('portal.nav.company') })
const api = useSokan()
const toast = useToast()
const errorMessage = useErrorMessage()
const { me, refresh: refreshMe } = useAuth()
const { modes, load } = useModes()

const form = ref<Record<string, any> | null>(null)
const saving = ref(false)
const uploading = ref('')

onMounted(async () => {
  load()
  form.value = await api.partner.profile()
})

function toggle(list: string[], v: string) {
  const i = list.indexOf(v)
  i >= 0 ? list.splice(i, 1) : list.push(v)
}

const newCountry = ref<string | null>(null)
watch(newCountry, (c) => {
  if (c && form.value && !form.value.coverage.includes(c)) form.value.coverage.push(c)
  newCountry.value = null
})

async function upload(field: 'logo' | 'cover_image', e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file || !form.value) return
  uploading.value = field
  try {
    form.value[field] = await uploadFile(file, { csrf: me.value?.csrf_token })
  } catch (err) {
    toast.error(errorMessage(err))
  } finally {
    uploading.value = ''
  }
}

async function save() {
  if (!form.value) return
  saving.value = true
  try {
    form.value = await api.partner.updateProfile(form.value)
    await refreshMe()
    toast.success(t('common.saved'))
  } catch (e) {
    toast.error(errorMessage(e))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <PortalHeading :title="$t('portal.nav.company')">
      <AppButton v-if="form?.status === 'Active'" :to="`/forwarders/${form.slug}`" variant="secondary" icon="external-link">{{ $t('partner.viewPublic') }}</AppButton>
    </PortalHeading>

    <div v-if="!form" class="skeleton h-[600px]" />
    <form v-else class="space-y-6" @submit.prevent="save">
      <section class="card overflow-hidden p-0">
        <div class="relative h-36 bg-night-950 sm:h-44">
          <img v-if="form.cover_image" :src="form.cover_image" alt="" class="size-full object-cover" />
          <AuroraBackground v-else :grid="false" />
          <label class="absolute end-3 bottom-3 inline-flex cursor-pointer items-center gap-1.5 rounded-xl bg-black/50 px-3 py-1.5 text-xs font-semibold text-white backdrop-blur hover:bg-black/70">
            <AppIcon :name="uploading === 'cover_image' ? 'loader' : 'upload'" :size="14" :class="uploading === 'cover_image' && 'animate-spin'" /> {{ $t('partner.cover') }}
            <input type="file" accept="image/*" class="sr-only" @change="upload('cover_image', $event)" />
          </label>
        </div>
        <div class="flex flex-wrap items-end gap-4 px-6 pb-6">
          <label class="relative -mt-10 cursor-pointer">
            <CompanyAvatar :name="form.company_name || '?'" :logo="form.logo" size="xl" class="ring-4 ring-surface" />
            <span class="absolute -end-1 -bottom-1 grid size-8 place-items-center rounded-full bg-brand text-white shadow"><AppIcon :name="uploading === 'logo' ? 'loader' : 'upload'" :size="14" :class="uploading === 'logo' && 'animate-spin'" /></span>
            <input type="file" accept="image/*" class="sr-only" @change="upload('logo', $event)" />
          </label>
          <div class="pb-1">
            <p class="text-lg font-bold">{{ form.company_name }}</p>
            <StatusPill :status="form.status" />
          </div>
        </div>
      </section>

      <section class="card grid gap-5 p-6 sm:grid-cols-2">
        <h2 class="font-bold sm:col-span-2">{{ $t('partner.sections.identity') }}</h2>
        <FormField v-model="form.company_name" :label="$t('fields.companyName')" required />
        <FormField v-model="form.tagline" :label="$t('partner.tagline')" :hint="$t('partner.taglineHint')" />
        <FormField v-model="form.about" as="textarea" :rows="5" :label="$t('partner.about')" class="sm:col-span-2" />
        <FormField v-model.number="form.established_year" type="number" min="1900" :max="new Date().getFullYear()" :label="$t('partner.established')" />
        <FormField v-model="form.team_size" as="select" :label="$t('partner.teamSize')">
          <template #options><option value="">—</option><option v-for="s in ['1-10', '11-50', '51-200', '201-500', '500+']" :key="s" :value="s">{{ s }}</option></template>
        </FormField>
        <FormField v-model="form.certifications" as="textarea" :rows="3" :label="$t('partner.certifications')" :hint="$t('partner.certificationsHint')" class="sm:col-span-2" />
      </section>

      <section class="card p-6">
        <h2 class="font-bold">{{ $t('partner.sections.services') }}</h2>
        <p class="mt-1 text-sm text-muted">{{ $t('partner.servicesHint') }}</p>
        <div class="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          <button
            v-for="m in modes"
            :key="m.name"
            type="button"
            class="flex items-center gap-2 rounded-xl border-2 px-3 py-2.5 text-start text-sm font-semibold transition-all"
            :class="form.modes.includes(m.name) ? 'border-brand bg-brand/8 text-brand' : 'border-line hover:border-brand/30'"
            @click="toggle(form.modes, m.name)"
          >
            <AppIcon :name="m.icon" :size="17" /> {{ $t(`modes.${m.code}.name`) }}
          </button>
        </div>
        <h3 class="mt-8 font-bold">{{ $t('profile.coverage') }}</h3>
        <p class="mt-1 text-sm text-muted">{{ $t('partner.coverageHint') }}</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <span v-for="c in form.coverage" :key="c" class="inline-flex items-center gap-1.5 rounded-lg bg-sunken py-1 ps-3 pe-1 text-sm">
            {{ c }}
            <button type="button" class="grid size-6 place-items-center rounded-md hover:bg-danger/10 hover:text-danger" :aria-label="$t('common.remove')" @click="toggle(form.coverage, c)"><AppIcon name="x" :size="14" /></button>
          </span>
        </div>
        <div class="mt-3 max-w-xs"><CountrySelect v-model="newCountry" :placeholder="$t('partner.addCountry')" /></div>
      </section>

      <section class="card grid gap-5 p-6 sm:grid-cols-2">
        <h2 class="font-bold sm:col-span-2">{{ $t('partner.sections.contact') }}</h2>
        <FormField v-model="form.email" type="email" :label="$t('fields.email')" dir="ltr" required />
        <FormField v-model="form.phone" type="tel" :label="$t('fields.phone')" dir="ltr" />
        <FormField v-model="form.website" type="url" :label="$t('fields.website')" dir="ltr" />
        <FormField v-model="form.license_number" :label="$t('fields.license')" />
        <CountrySelect v-model="form.country" :label="$t('fields.country')" />
        <FormField v-model="form.city" :label="$t('fields.city')" />
        <FormField v-model="form.address" as="textarea" :rows="2" :label="$t('fields.address')" class="sm:col-span-2" />
      </section>

      <section class="card space-y-3 p-6">
        <h2 class="font-bold">{{ $t('partner.sections.notifications') }}</h2>
        <label class="flex items-center gap-3 text-sm"><input v-model="form.notify_new_requests" type="checkbox" :true-value="1" :false-value="0" class="size-5 accent-brand" /> {{ $t('partner.notifyRequests') }}</label>
        <label class="flex items-center gap-3 text-sm"><input v-model="form.notify_quote_updates" type="checkbox" :true-value="1" :false-value="0" class="size-5 accent-brand" /> {{ $t('partner.notifyQuotes') }}</label>
      </section>

      <section class="card p-6">
        <h2 class="font-bold">{{ $t('partner.sections.team') }}</h2>
        <ul class="mt-4 divide-y divide-line">
          <li v-for="m in form.members" :key="m.user" class="flex items-center justify-between gap-3 py-3 text-sm">
            <span><b>{{ m.full_name }}</b> <span class="text-faint" dir="ltr">{{ m.user }}</span></span>
            <span class="rounded-lg bg-sunken px-2 py-1 text-xs font-semibold">{{ $t(`partner.role.${m.role}`) }}</span>
          </li>
        </ul>
        <p class="mt-3 text-xs text-faint">{{ $t('partner.teamHint') }}</p>
      </section>

      <div class="glass sticky bottom-20 z-10 flex justify-end rounded-2xl p-3 lg:bottom-4">
        <AppButton type="submit" variant="primary" size="lg" :loading="saving" icon="check">{{ $t('common.saveChanges') }}</AppButton>
      </div>
    </form>
  </div>
</template>
