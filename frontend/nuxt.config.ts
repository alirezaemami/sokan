import tailwindcss from '@tailwindcss/vite'

// Origin of the Frappe backend — in development the `bench start` web
// server. Override per-environment with NUXT_PUBLIC_FRAPPE_API_BASE.
const frappeApiBase = process.env.NUXT_PUBLIC_FRAPPE_API_BASE || 'http://127.0.0.1:8000'

// One bench serves many sites. Frappe picks the site from the
// X-Frappe-Site-Name header before the Host header, so the proxy names it
// explicitly and works whatever the bench's default site is.
const frappeSiteName = process.env.NUXT_FRAPPE_SITE_NAME || 'sokan.local'
const toFrappe = (path: string) => ({ proxy: { to: `${frappeApiBase}${path}`, headers: { 'X-Frappe-Site-Name': frappeSiteName } } })

// Public canonical origin. Every absolute URL (sitemap, canonical, hreflang,
// OG tags) is built from this, so it must be the real domain in production.
const siteUrl = process.env.NUXT_PUBLIC_SITE_URL || 'https://www.sokan.net'

// Portals are personal, authenticated screens: render them in the browser
// only (no SSR auth round-trip) and keep them out of every index.
const portal = { ssr: false, robots: false } as const

export default defineNuxtConfig({
  compatibilityDate: '2026-10-01',
  devtools: { enabled: true },
  telemetry: false,

  // Marketing pages and the forwarder directory are server-rendered so
  // crawlers get complete markup on first byte.
  ssr: true,

  modules: ['@nuxtjs/i18n', '@nuxtjs/seo', '@nuxt/image', '@vueuse/nuxt', 'motion-v/nuxt'],

  // Flat component names (<AppButton>, not <UiAppButton>); folders are for humans.
  components: [{ path: '~/components', pathPrefix: false }],

  css: ['~/assets/css/main.css'],

  vite: {
    plugins: [tailwindcss()],
  },

  runtimeConfig: {
    frappeSiteName,
    public: {
      frappeApiBase,
      siteUrl,
    },
  },

  site: {
    url: siteUrl,
    name: 'Sokan',
    description:
      'Sokan is the freight marketplace where shippers post one request and verified forwarders compete with real quotes for sea, air, road and rail.',
    defaultLocale: 'en',
  },

  i18n: {
    baseUrl: siteUrl,
    defaultLocale: 'en',
    strategy: 'prefix_except_default',
    locales: [
      { code: 'en', language: 'en-US', name: 'English', dir: 'ltr', file: 'en.json' },
      { code: 'fa', language: 'fa-IR', name: 'فارسی', dir: 'rtl', file: 'fa.json' },
    ],
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'sokan_lang',
      redirectOn: 'root',
    },
  },

  // Same-origin API: the browser only ever talks to this app, which proxies
  // /api and /files to Frappe. No CORS, the Frappe session cookie just works,
  // and it mirrors the production nginx layout.
  routeRules: {
    '/api/**': toFrappe('/api/**'),
    '/files/**': toFrappe('/files/**'),
    '/private/files/**': toFrappe('/private/files/**'),

    '/account/**': portal,
    '/partner/**': portal,
    '/admin': portal,
    '/admin/**': portal,
    '/fa/account/**': portal,
    '/fa/partner/**': portal,
    '/fa/admin': portal,
    '/fa/admin/**': portal,
    '/login': { robots: false },
    '/fa/login': { robots: false },
    '/forgot-password': { robots: false },
    '/fa/forgot-password': { robots: false },
    '/verify-email': portal,
    '/fa/verify-email': portal,

    // Directory pages change rarely; serve them stale while revalidating.
    '/forwarders/**': { swr: 300 },
    '/fa/forwarders/**': { swr: 300 },
  },

  app: {
    head: {
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1, viewport-fit=cover' },
        { name: 'theme-color', content: '#e7eff0', media: '(prefers-color-scheme: light)' },
        { name: 'theme-color', content: '#08202a', media: '(prefers-color-scheme: dark)' },
        { name: 'format-detection', content: 'telephone=no' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
        // Browsers and crawlers that don't take SVG icons (Safari tabs, some search results).
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico', sizes: '48x48' },
        { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' },
        { rel: 'manifest', href: '/site.webmanifest' },
      ],
      // Apply the stored theme before first paint so dark-mode users never see a flash.
      script: [
        {
          innerHTML:
            "try{var t=localStorage.getItem('sokan-theme');var d=t?t==='dark':matchMedia('(prefers-color-scheme: dark)').matches;document.documentElement.classList.toggle('dark',d)}catch(e){}",
          tagPosition: 'head',
        },
      ],
    },
    pageTransition: { name: 'page', mode: 'out-in' },
  },

  image: {
    domains: [new URL(frappeApiBase).hostname, new URL(siteUrl).hostname],
    format: ['webp'],
  },

  sitemap: {
    // Forwarder slugs live in Frappe. Deliberately not under /api — the proxy
    // rule above would swallow it.
    sources: ['/__sitemap__/urls'],
    exclude: ['/account/**', '/partner/**', '/admin', '/admin/**', '/login', '/register/**', '/forgot-password', '/reset-password'],
  },

  robots: {
    disallow: ['/api/', '/account/', '/partner/', '/admin'],
  },

  // Share cards come from public/og-default.jpg; runtime OG rendering is
  // slow to boot and unreliable at shaping Persian text.
  ogImage: { enabled: false },

  schemaOrg: {
    identity: {
      type: 'Organization',
      name: 'Sokan',
      url: siteUrl,
      logo: `${siteUrl}/logo.png`,
    },
  },

  nitro: {
    preset: 'node-server',
    compressPublicAssets: { brotli: true, gzip: true },
  },

  experimental: {
    payloadExtraction: true,
  },

  typescript: { strict: true },
})
