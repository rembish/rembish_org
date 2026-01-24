import { TypeAnimation } from 'react-type-animation'
import {
  BiLogoLinkedinSquare,
  BiLogoGithub,
  BiLogoInstagramAlt,
  BiLogoFacebookSquare,
} from 'react-icons/bi'
import { FaXTwitter } from 'react-icons/fa6'

const typedItems = [
  'a Senior Team Leader',
  2000,
  'a Python professional',
  2000,
  'an IT Manager',
  2000,
  'a Traveller',
  2000,
  'an Aerial Photographer',
  2000,
  'a Drone Pilot',
  2000,
]

const socialLinks = [
  { href: 'https://linkedin.com/in/rembish/', icon: BiLogoLinkedinSquare },
  { href: 'https://github.com/rembish', icon: BiLogoGithub },
  { href: 'https://instagram.com/arembish/', icon: BiLogoInstagramAlt },
  { href: 'https://x.com/rembish', icon: FaXTwitter },
  { href: 'https://facebook.com/rembish/', icon: BiLogoFacebookSquare },
]

export default function Home() {
  return (
    <section id="hero">
      <div className="container">
        <h1>Alex Rembish</h1>
        <p>
          I'm{' '}
          <TypeAnimation
            sequence={typedItems}
            wrapper="span"
            className="typed"
            repeat={Infinity}
            speed={50}
            deletionSpeed={80}
          />
        </p>
        <div className="social-links">
          {socialLinks.map(({ href, icon: Icon }) => (
            <a key={href} href={href} target="_blank" rel="noopener noreferrer">
              <Icon />
            </a>
          ))}
        </div>
      </div>
    </section>
  )
}
