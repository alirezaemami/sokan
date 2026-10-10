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
