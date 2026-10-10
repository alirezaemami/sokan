export interface Toast {
  id: number
  kind: 'success' | 'error' | 'info'
  text: string
}

let seq = 0

export function useToast() {
  const toasts = useState<Toast[]>('sokan-toasts', () => [])

  function push(kind: Toast['kind'], text: string, ms = 4200) {
    const id = ++seq
    toasts.value = [...toasts.value, { id, kind, text }]
    if (import.meta.client) setTimeout(() => dismiss(id), ms)
  }

  function dismiss(id: number) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  return {
    toasts,
    dismiss,
    success: (text: string) => push('success', text),
    error: (text: string) => push('error', text, 6000),
    info: (text: string) => push('info', text),
  }
}
