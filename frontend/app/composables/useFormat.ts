/**
 * Locale-aware formatting. Everything goes through Intl, so Persian gets
 * Persian digits and RTL-correct currency placement for free.
 */
export function useFormat() {
  const { locale, t, te } = useI18n()
  const intlLocale = computed(() => (locale.value === 'fa' ? 'fa-IR' : 'en-US'))

  const regionNames = computed(() => {
    try {
      return new Intl.DisplayNames([intlLocale.value], { type: 'region' })
    } catch {
      return null
    }
  })

  function number(v: number | null | undefined, digits = 0) {
    return new Intl.NumberFormat(intlLocale.value, { maximumFractionDigits: digits }).format(Number(v) || 0)
  }

  function compact(v: number | null | undefined) {
    return new Intl.NumberFormat(intlLocale.value, { notation: 'compact', maximumFractionDigits: 1 }).format(Number(v) || 0)
  }

  function money(v: number | null | undefined, currency = 'USD', digits?: number) {
    const amount = Number(v) || 0
    try {
      return new Intl.NumberFormat(intlLocale.value, {
        style: 'currency',
        currency,
        maximumFractionDigits: digits ?? (Number.isInteger(amount) ? 0 : 2),
      }).format(amount)
    } catch {
      return `${number(amount, 2)} ${currency}`
    }
  }

  function date(v: string | Date | null | undefined, style: 'short' | 'medium' | 'long' = 'medium') {
    if (!v) return '—'
    const d = typeof v === 'string' ? new Date(v.replace(' ', 'T')) : v
    if (Number.isNaN(d.getTime())) return '—'
    return new Intl.DateTimeFormat(intlLocale.value, { dateStyle: style }).format(d)
  }

  function relative(v: string | Date | null | undefined) {
    if (!v) return ''
    const d = typeof v === 'string' ? new Date(v.replace(' ', 'T')) : v
    const diff = (d.getTime() - Date.now()) / 1000
    const rtf = new Intl.RelativeTimeFormat(intlLocale.value, { numeric: 'auto' })
    const units: [Intl.RelativeTimeFormatUnit, number][] = [
      ['year', 31536000],
      ['month', 2592000],
      ['week', 604800],
      ['day', 86400],
      ['hour', 3600],
      ['minute', 60],
    ]
    for (const [unit, secs] of units) {
      if (Math.abs(diff) >= secs) return rtf.format(Math.round(diff / secs), unit)
    }
    return rtf.format(Math.round(diff), 'second')
  }

  /** Country name in the visitor's language; Frappe stores English names. */
  function country(code: string | null | undefined, fallback?: string | null) {
    if (!code) return fallback || ''
    try {
      return regionNames.value?.of(code.toUpperCase()) || fallback || code
    } catch {
      return fallback || code
    }
  }

  function flag(code: string | null | undefined) {
    if (!code || code.length !== 2) return '🌐'
    return String.fromCodePoint(...[...code.toUpperCase()].map((c) => 0x1f1a5 + c.charCodeAt(0)))
  }

  function place(p: { city?: string | null; country?: string | null; country_code?: string | null } | null | undefined) {
    if (!p) return ''
    const c = country(p.country_code, p.country)
    return p.city ? `${p.city}, ${c}` : c
  }

  /** Translate a backend enum value (status, category…) with graceful fallback. */
  function label(group: string, value: string | null | undefined) {
    if (!value) return ''
    const key = `${group}.${value}`
    return te(key) ? t(key) : value
  }

  function weight(kg: number | null | undefined) {
    const v = Number(kg) || 0
    return v >= 1000 ? `${number(v / 1000, 2)} ${t('units.t')}` : `${number(v, 0)} ${t('units.kg')}`
  }

  return { intlLocale, number, compact, money, date, relative, country, flag, place, label, weight }
}
