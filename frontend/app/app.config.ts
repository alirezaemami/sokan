import type { HomeStat } from '~/types/sokan'

/**
 * Site content that changes without code: edit the values here and redeploy.
 * Anything left empty is simply not shown, so nothing placeholder ever ships.
 */
export default defineAppConfig({
  home: {
    /**
     * The four blocks under the hero. `value` animates up to the number;
     * `text` is shown as-is; `icon` + `textKey` replace the number with an
     * icon and a short line. `modes` uses the live transport-mode count.
     * Swap in real network numbers here once they are worth showing.
     */
    stats: [
      { key: 'home.stats.costForShippers', text: '$0' },
      { key: 'home.stats.modes', value: 'modes' as number | 'modes', fallback: 8 },
      { key: 'home.stats.alwaysOn', value: 24, suffix: '/7' },
      { key: 'home.stats.private', icon: 'lock', textKey: 'home.stats.privateText' },
    ] as HomeStat[],
    /** "Providers on Sokan" shows only with at least this many verified providers. */
    featuredMinProviders: 3,
  },

  /**
   * Company and contact details for the trust block on the home page (and
   * later the footer). Empty items are hidden; the block is hidden entirely
   * while everything is empty.
   */
  trust: {
    companyName: '',
    address: '',
    phone: '',
    email: '',
    /** e.g. { name: 'WhatsApp', url: 'https://wa.me/98…' } */
    messengers: [] as { name: string; url: string }[],
    /** Trust badge (e.g. Enamad) embed code, exactly as issued. */
    badgeHtml: '',
    /** Show the About us link once the page has real content. */
    showAbout: false,
  },
})
