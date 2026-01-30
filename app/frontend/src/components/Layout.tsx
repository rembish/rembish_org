import { useState } from "react";
import { NavLink, Link } from "react-router-dom";
import {
  BiHome,
  BiFileBlank,
  BiLayer,
  BiImage,
  BiGlobe,
  BiEnvelope,
  BiMenu,
  BiX,
  BiLogIn,
  BiLogOut,
  BiCog,
} from "react-icons/bi";
import { SiAnthropic } from "react-icons/si";
import { useAuth } from "../hooks/useAuth";
import { version } from "../../package.json";

interface LayoutProps {
  children: React.ReactNode;
}

const navItems = [
  { to: "/", icon: BiHome, label: "Home" },
  { to: "/cv", icon: BiFileBlank, label: "Curriculum Vitae" },
  { to: "/projects", icon: BiLayer, label: "Projects" },
  { to: "/photos", icon: BiImage, label: "Photos" },
  { to: "/travels", icon: BiGlobe, label: "Travels" },
  { to: "/contact", icon: BiEnvelope, label: "Contact" },
];

export default function Layout({ children }: LayoutProps) {
  const [mobileNavActive, setMobileNavActive] = useState(false);
  const { user, loading, login, logout } = useAuth();

  const toggleMobileNav = () => setMobileNavActive(!mobileNavActive);
  const closeMobileNav = () => setMobileNavActive(false);

  return (
    <>
      <button
        type="button"
        className="mobile-nav-toggle"
        onClick={toggleMobileNav}
      >
        {mobileNavActive ? <BiX /> : <BiMenu />}
      </button>

      <header
        id="header"
        className={mobileNavActive ? "mobile-nav-active" : ""}
      >
        <nav>
          <ul className="nav-menu">
            {navItems.map(({ to, icon: Icon, label }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  className={({ isActive }) => (isActive ? "active" : "")}
                  onClick={closeMobileNav}
                >
                  <span className="nav-icon">
                    <Icon />
                  </span>
                  <span className="nav-label">{label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
          {!loading && (
            <ul className="nav-menu nav-menu-auth">
              {user?.is_admin && (
                <li>
                  <NavLink
                    to="/admin"
                    className={({ isActive }) => (isActive ? "active" : "")}
                    onClick={closeMobileNav}
                  >
                    <span className="nav-icon">
                      <BiCog />
                    </span>
                    <span className="nav-label">Admin</span>
                  </NavLink>
                </li>
              )}
              <li>
                {user ? (
                  <button onClick={logout} className="nav-auth-btn">
                    <span className="nav-icon">
                      <BiLogOut />
                    </span>
                    <span className="nav-label">Logout</span>
                  </button>
                ) : (
                  <button onClick={login} className="nav-auth-btn">
                    <span className="nav-icon">
                      <BiLogIn />
                    </span>
                    <span className="nav-label">Login</span>
                  </button>
                )}
              </li>
            </ul>
          )}
        </nav>
      </header>

      <main id="main">{children}</main>

      <footer id="footer">
        <div className="copyright">
          Content copyright &copy; <strong>Alex Rembish</strong> 2013&ndash;
          {new Date().getFullYear()} (
          <Link to="/changelog" className="version-link">
            v{version}
          </Link>
          )
        </div>
        <div className="credits">
          Source code on{" "}
          <a href="https://github.com/rembish/rembish_org">GitHub</a>, built
          with <SiAnthropic className="claude-icon" />{" "}
          <a href="https://claude.ai">Claude</a>
        </div>
      </footer>
    </>
  );
}
