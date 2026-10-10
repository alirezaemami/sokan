import type { AdminOverview } from '~/types/sokan'

/**
 * Counts of work waiting for a manager (pending forwarders, top-ups,
 * reviews, new messages). Shared by the nav badges and the pages that clear
 * them, so approving something updates the badge at once.
 */
export function useAdminAttention() {
  const counts = useState<AdminOverview['attention'] | null>('admin-attention', () => null)
  const api = useSokan()
  async function refresh() {
    try {
      counts.value = await api.admin.attention()
    } catch {
      // Badges are a convenience; a failed refresh keeps the last counts.
    }
  }
  return { counts, refresh }
}
