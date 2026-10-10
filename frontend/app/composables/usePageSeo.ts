interface PageSeoInput {
  title: string
  description?: string | null
  image?: string | null
  type?: 'website' | 'article' | 'profile'
  noIndex?: boolean
}

/**
 * One place where every page's SEO tags are assembled. Canonical, hreflang
 * alternates and <html lang/dir> come from useLocaleHead in app.vue, so
 * pages only describe themselves here.
 */
export function usePageSeo(input: MaybeRefOrGetter<PageSeoInput>) {
  const { siteUrl } = useRuntimeConfig().public
  const { t } = useI18n()

  const seo = computed(() => {
    const v = toValue(input)
    const description = (v.description || t('seo.defaultDescription')).replace(/\s+/g, ' ').trim().slice(0, 160)
    const raw = v.image
    // OG images must be absolute and raster — social crawlers drop SVG and relative URLs.
    const image = raw ? (raw.startsWith('http') ? raw : `${siteUrl}${raw}`) : `${siteUrl}/og-default.jpg`
    return { title: v.title, description, image, type: v.type ?? 'website', noIndex: Boolean(v.noIndex) }
  })

  useSeoMeta({
    title: () => seo.value.title,
    description: () => seo.value.description,
    ogTitle: () => seo.value.title,
    ogDescription: () => seo.value.description,
    ogImage: () => seo.value.image,
    ogImageAlt: () => seo.value.title,
    // Dimensions let platforms lay out the card without fetching the image first.
    ogImageWidth: () => (toValue(input).image ? undefined : 1200),
    ogImageHeight: () => (toValue(input).image ? undefined : 630),
    ogImageType: () => (toValue(input).image ? undefined : 'image/jpeg'),
    ogSiteName: 'Sokan',
    ogType: () => seo.value.type as 'website',
    twitterCard: 'summary_large_image',
    twitterTitle: () => seo.value.title,
    twitterDescription: () => seo.value.description,
    twitterImage: () => seo.value.image,
    robots: () => (seo.value.noIndex ? 'noindex, nofollow' : 'index, follow, max-image-preview:large, max-snippet:-1'),
  })

  return seo
}

/** BreadcrumbList structured data — rendered by Google as the result's path. */
export function useBreadcrumbs(items: MaybeRefOrGetter<{ name: string; item: string }[]>) {
  useSchemaOrg([defineBreadcrumb({ itemListElement: toValue(items) })])
}
