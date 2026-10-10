<script setup lang="ts">
// <html lang/dir>, canonical and hreflang alternates for every page.
const head = useLocaleHead({ dir: true, lang: true, seo: true })
const { t } = useI18n()

useHead(() => ({
  htmlAttrs: head.value.htmlAttrs,
  link: head.value.link,
  meta: head.value.meta,
  titleTemplate: (title?: string) => {
    if (!title) return t('seo.homeTitle')
    return title.includes(t('seo.brand')) ? title : `${title} · ${t('seo.brand')}`
  },
}))

// Resolve the session once on the client; portals and the header read it.
const { ensure } = useAuth()
onMounted(() => ensure())
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
  <AppToasts />
</template>
