import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { BiHome, BiFileBlank, BiEnvelope, BiMenu, BiX } from 'react-icons/bi'

interface LayoutProps {
  children: React.ReactNode
}

const navItems = [
  { to: '/', icon: BiHome, label: 'Home' },
  { to: '/cv', icon: BiFileBlank, label: 'Curriculum Vitae' },
  { to: '/contact', icon: BiEnvelope, label: 'Contact' },
]

export default function Layout({ children }: LayoutProps) {
  const [mobileNavActive, setMobileNavActive] = useState(false)

  const toggleMobileNav = () => setMobileNavActive(!mobileNavActive)
  const closeMobileNav = () => setMobileNavActive(false)

  return (
    <>
      <button
        type="button"
        className="mobile-nav-toggle"
        onClick={toggleMobileNav}
      >
        {mobileNavActive ? <BiX /> : <BiMenu />}
      </button>

      <header id="header" className={mobileNavActive ? 'mobile-nav-active' : ''}>
        <nav>
          <ul className="nav-menu">
            {navItems.map(({ to, icon: Icon, label }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  className={({ isActive }) => isActive ? 'active' : ''}
                  onClick={closeMobileNav}
                >
                  <span className="nav-icon"><Icon /></span>
                  <span className="nav-label">{label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </header>

      <main id="main">{children}</main>

      <footer id="footer">
        <div className="copyright">
          Content copyright &copy; <strong>Alex Rembish</strong> 2013&ndash;{new Date().getFullYear()}
        </div>
        <div className="credits">
          Source code can be found on{' '}
          <a href="https://github.com/rembish/rembish_org">GitHub</a>
        </div>
      </footer>
    </>
  )
}
