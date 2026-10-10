/** Light/dark toggle. The inline head script applies the stored choice before first paint. */
export function useTheme() {
  const dark = useState('sokan-dark', () => false)

  onMounted(() => {
    dark.value = document.documentElement.classList.contains('dark')
  })

  function toggle() {
    dark.value = !dark.value
    document.documentElement.classList.toggle('dark', dark.value)
    try {
      localStorage.setItem('sokan-theme', dark.value ? 'dark' : 'light')
    } catch {
      // Private mode — the choice just won't persist.
    }
  }

  return { dark, toggle }
}
