/**
 * Dynamic sitemap entries: every active forwarder profile, in both locales.
 * Deliberately not under /api — the proxy rule would swallow it.
 */
export default defineSitemapEventHandler(async () => {
  const { frappeApiBase } = useRuntimeConfig().public
  try {
    const res = await $fetch<{ message: { slug: string; modified: string }[] }>(
      `${frappeApiBase}/api/method/sokan.api.public.sitemap_urls`,
    )
    return res.message.map((f) => ({
      loc: `/forwarders/${f.slug}`,
      lastmod: f.modified,
      _i18nTransform: true,
    }))
  } catch {
    return []
  }
})
