import { useState, useCallback } from "react";
import { TypeAnimation } from "react-type-animation";
import {
  BiLogoLinkedinSquare,
  BiLogoGithub,
  BiLogoInstagramAlt,
  BiLogoFacebookSquare,
} from "react-icons/bi";
import { FaXTwitter } from "react-icons/fa6";
import LocationButton from "../components/LocationButton";

const socialLinks = [
  { href: "https://linkedin.com/in/rembish/", icon: BiLogoLinkedinSquare },
  { href: "https://github.com/rembish", icon: BiLogoGithub },
  { href: "https://instagram.com/arembish/", icon: BiLogoInstagramAlt },
  { href: "https://x.com/rembish", icon: FaXTwitter },
  { href: "https://facebook.com/rembish/", icon: BiLogoFacebookSquare },
];

export default function Home() {
  const [cosplayBg, setCosplayBg] = useState(false);

  const typedItems = useCallback((): (string | number | (() => void))[] => {
    const show = () => setCosplayBg(true);
    const hide = () => setCosplayBg(false);
    return [
      "a Senior Team Leader",
      2000,
      hide,
      "a Python Developer",
      2000,
      "an IT Manager",
      2000,
      "a Traveler",
      2000,
      "an Aerial Photographer",
      2000,
      "a Drone Pilot",
      2000,
      show,
      "an amateur Cosplayer",
      2000,
      hide,
    ];
  }, []);

  return (
    <>
      <section id="hero" className={cosplayBg ? "hero-cosplay" : ""}>
        <div className="container">
          <h1>Alex Rembish</h1>
          <p>
            I'm{" "}
            <TypeAnimation
              sequence={typedItems()}
              wrapper="span"
              className="typed"
              repeat={Infinity}
              speed={50}
              deletionSpeed={80}
            />
          </p>
          <div className="social-links">
            {socialLinks.map(({ href, icon: Icon }) => (
              <a
                key={href}
                href={href}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Icon />
              </a>
            ))}
          </div>
        </div>
      </section>
      <LocationButton />
    </>
  );
}
