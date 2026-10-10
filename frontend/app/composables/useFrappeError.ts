/**
 * Turn a Frappe error response into a sentence worth showing a person.
 *
 * Validation failures arrive as `_server_messages` — a JSON string holding an
 * array of JSON strings, each with a `message`. Those come from our own
 * `frappe.throw(_("…"))` calls, so they're safe to surface. Tracebacks and
 * exception types are swallowed.
 */
export function frappeErrorMessage(err: unknown, fallback: string): string {
  const e = err as {
    data?: Record<string, unknown>
    response?: { _data?: Record<string, unknown>; status?: number }
    statusCode?: number
    status?: number
  }
  const data = e?.data ?? e?.response?._data

  const raw = data?._server_messages
  if (typeof raw === 'string') {
    try {
      const first = (JSON.parse(raw) as string[])[0]
      if (first) {
        const parsed = JSON.parse(first) as { message?: string }
        if (parsed?.message) return stripTags(parsed.message)
      }
    } catch {
      // Malformed payload — fall through.
    }
  }
  if (typeof data?.message === 'string' && data.exc_type) return stripTags(data.message)

  const status = e?.statusCode ?? e?.status ?? e?.response?.status
  if (status === 401 && typeof data?.message === 'string') return stripTags(data.message)
  return fallback
}

export function useErrorMessage() {
  const { t } = useI18n()
  return (err: unknown, fallback?: string) => {
    const status = (err as { statusCode?: number })?.statusCode
    if (status === 429) return t('errors.rateLimited')
    return frappeErrorMessage(err, fallback ?? t('errors.generic'))
  }
}

function stripTags(html: string) {
  return html.replace(/<[^>]+>/g, '').trim()
}
