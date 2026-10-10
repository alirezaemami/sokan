import type { Country, TransportMode } from '~/types/sokan'

/** Countries load once per session and are shared by every picker on the page. */
export function useCountries() {
  const list = useState<Country[]>('sokan-countries', () => [])
  const api = useSokan()
  if (import.meta.client && !list.value.length) {
    api
      .countries()
      .then((c) => (list.value = c))
      .catch(() => {})
  }
  return list
}

/** Transport modes, cached the same way. */
export function useModes() {
  const list = useState<TransportMode[]>('sokan-modes', () => [])
  const api = useSokan()
  const load = async () => {
    if (!list.value.length) list.value = await api.modes()
    return list.value
  }
  return { modes: list, load }
}

/** Localised label for a Frappe Country name ("Iran" → "ایران" in Persian), with its flag. */
export function useCountryLabel() {
  const countries = useCountries()
  const fmt = useFormat()
  const codes = computed(() => new Map(countries.value.map((c) => [c.name, c.code])))
  return (name: string | null | undefined, opts: { flag?: boolean } = {}) => {
    if (!name) return ''
    const code = codes.value.get(name)
    const label = fmt.country(code, name)
    return opts.flag && code ? `${fmt.flag(code)} ${label}` : label
  }
}
