import { useEffect, useState } from 'react'

const prefersDark = () => window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches

export default function ThemeToggle() {
  const [dark, setDark] = useState<boolean>(() => {
    const saved = localStorage.getItem('cm_theme')
    if (saved) return saved === 'dark'
    return prefersDark()
  })

  useEffect(() => {
    const root = document.documentElement
    if (dark) {
      root.classList.add('dark')
      localStorage.setItem('cm_theme', 'dark')
    } else {
      root.classList.remove('dark')
      localStorage.setItem('cm_theme', 'light')
    }
  }, [dark])

  return (
    <button
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="btn-ghost flex items-center gap-2"
      onClick={() => setDark((d) => !d)}
    >
      <span className="inline-block w-5 h-5">
        {dark ? (
          // sun
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5"><path d="M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12Z"/><path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>
        ) : (
          // moon
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z"/></svg>
        )}
      </span>
      <span className="hidden sm:block text-sm">{dark ? 'Light' : 'Dark'}</span>
    </button>
  )
}
