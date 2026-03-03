import {
  BiGlobe,
  BiCodeAlt,
  BiLinkExternal,
  BiLogoGithub,
  BiSolidStar,
} from "react-icons/bi";
import { SiNpm, SiPypi } from "react-icons/si";

interface Package {
  name: string;
  npmUrl: string;
  githubUrl: string;
}

interface Project {
  title: string;
  description: string;
  logo?: string;
  starred?: boolean;
  features: string[];
  techStack: string[];
  status: "active" | "completed" | "alpha" | "beta";
  links: { label: string; url: string; icon: React.ComponentType }[];
  packages?: Package[];
}

const projects: Project[] = [
  {
    title: "rembish.org",
    description:
      "This very website! What started as a simple portfolio page grew into a full travel management platform — trip planning, flight tracking, encrypted document vault, photo gallery, and more. Built entirely with Claude AI.",
    features: [
      "Interactive travel map with 193 UN countries and 330 TCC destinations",
      "Flight tracking with AeroDataBox lookup and statistics",
      "Encrypted vault for passports, visas, and travel documents",
      "Instagram photo gallery with country-based world map",
      "Trip planner with country info, weather, holidays, and vacation balance",
      "Car rental, transport booking, and accommodation management",
    ],
    techStack: [
      "React",
      "TypeScript",
      "Vite",
      "FastAPI",
      "SQLAlchemy",
      "Google Cloud",
    ],
    status: "active",
    links: [
      { label: "Website", url: "https://rembish.org", icon: BiLinkExternal },
      {
        label: "GitHub",
        url: "https://github.com/rembish/rembish_org",
        icon: BiLogoGithub,
      },
    ],
  },
  {
    title: "Deploy Horoscope",
    description:
      "Should I deploy today? Let the stars decide. A deterministic deployment oracle that answers the eternal question using your zodiac sign, moon phase, Mercury retrograde status, planetary positions, and the iron law that Fridays are always red. No database. No real astrology. Now with a JSON API.",
    features: [
      "12 zodiac signs with optional birthdate for extra cosmic calibration",
      "Deterministic SHA-256 scores — same inputs always produce the same result",
      "Animated SVG natal chart with zodiac ring, house sectors, and aspect lines",
      "Two-month deployment calendar with progressive color reveals",
      "Stable shareable URLs — date encoded as mystical spell-words, no DB needed",
      "JSON API with rate limiting for integrations and bots",
      "OG share card PNG generation for rich link previews",
      "Special-day themes: Halloween, Christmas, birthday, Friday the 13th, and more",
    ],
    techStack: ["Python 3.12+", "FastAPI", "Jinja2", "Pillow", "SVG"],
    status: "active",
    links: [
      {
        label: "Website",
        url: "https://deployhoroscope.com",
        icon: BiLinkExternal,
      },
    ],
  },
  {
    title: "TripClimate",
    description:
      "A travel event calendar that shows what awaits before you book. Given a country and date range, it layers 7 data sources — cultural events, sporting events, public holidays, religious observances, weather, seasonality, and travel warnings — each tagged with whether it's a reason to go or a reason to stay away. Covers 250 countries with GeoIP-based country detection, shareable URLs, and a world events map.",
    features: [
      "330 cultural events across 167 countries: Ramadan, Carnival, Songkran, Holi, Nyepi, Oktoberfest, and more",
      "194 sporting events: F1, Grand Slams, marathons, Olympics, cycling tours",
      "Public holidays for 240+ countries with 3-tier resolution fallback",
      "Historical weather averages, extreme condition alerts, closed seasons, and seasonality indicators",
      "Travel warnings from US State Dept and Canada government advisories",
      "Travel Score — Explorer/Chill modes to surface trips that match your style",
      "World choropleth map, shareable URLs, and OG preview cards",
    ],
    techStack: ["Python", "FastAPI", "Alpine.js", "Google Cloud Run"],
    status: "beta",
    links: [
      {
        label: "Website",
        url: "https://tripclimate.com",
        icon: BiLinkExternal,
      },
    ],
  },
  {
    title: "Am I Free?",
    description:
      "A web application that helps you plan your vacation days by calculating working days spent on trips, excluding weekends and public holidays automatically.",
    logo: "/amifree-logo.svg",
    features: [
      "Calculate vacation days needed for trips",
      "Exclude weekends and public holidays automatically",
      "Track multiple trips throughout the year",
      "View remaining vacation days",
      "What-if calculator for planning future trips",
      "Support for multiple countries",
    ],
    techStack: [
      "React",
      "TypeScript",
      "Vite",
      "Mantine UI",
      "FastAPI",
      "SQLAlchemy",
      "MySQL",
      "Google Cloud",
    ],
    status: "alpha",
    links: [
      { label: "Website", url: "https://amifree.info", icon: BiLinkExternal },
    ],
  },
  {
    title: "pydjirecord",
    description:
      "A Python 3.12+ parser for DJI drone flight log files (.txt binary format). Handles format versions 1–14 with XOR and AES-256-CBC decryption. Built as a rewrite of the Rust dji-log-parser, with improvements: zero-coordinate backfill from OSD GPS frames, accurate video/photo/distance stats from raw telemetry, and local keychain caching for the DJI API.",
    features: [
      "Parse DJI flight logs across format versions 1–14",
      "XOR + AES-256-CBC decryption with DJI API keychain fetching",
      "Multiple output formats: JSON, GeoJSON, KML, CSV",
      "Zero-coordinate backfill from OSD GPS telemetry frames",
      "Accurate photo count, video time, and distance from raw records",
    ],
    techStack: ["Python 3.12+", "PyCryptodome", "httpx"],
    status: "active",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/pydjirecord",
        icon: BiLogoGithub,
      },
      {
        label: "PyPI",
        url: "https://pypi.org/project/pydjirecord/",
        icon: SiPypi,
      },
      {
        label: "Docs",
        url: "https://rembish.github.io/pydjirecord/",
        icon: BiLinkExternal,
      },
    ],
  },
  {
    title: "TopoJSON Maps",
    description:
      "Three open-source TopoJSON world maps built from Natural Earth 10m shapefiles — one for each major travel tracking system, plus a standard ISO baseline. All published on npm and available via CDN.",
    features: [
      "ISO A2 — 250 polygons keyed by ISO 3166-1 alpha-2 codes, overseas territories as separate polygons",
      "TCC — 330 destinations matching the Travelers' Century Club list (no equivalent existed before)",
      "NM UN+ — 265 regions matching the NomadMania UN+ destination list",
      "Full and markers variants: tiny territories rendered as point markers in compact builds",
      "Transcontinental splits, disputed territories, island extractions, Antarctic claim sectors",
    ],
    techStack: ["Python", "Shapely", "GeoPandas", "mapshaper", "TopoJSON"],
    status: "active",
    links: [],
    packages: [
      {
        name: "@rembish/iso-topojson",
        npmUrl: "https://www.npmjs.com/package/@rembish/iso-topojson",
        githubUrl: "https://github.com/rembish/iso-topojson",
      },
      {
        name: "@rembish/tcc-topojson",
        npmUrl: "https://www.npmjs.com/package/@rembish/tcc-topojson",
        githubUrl: "https://github.com/rembish/tcc-topojson",
      },
      {
        name: "@rembish/nm-unp-topojson",
        npmUrl: "https://www.npmjs.com/package/@rembish/nm-unp-topojson",
        githubUrl: "https://github.com/rembish/nm-unp-topojson",
      },
    ],
  },
  {
    title: "TextAtAnyCost",
    description:
      "One of my oldest and most popular open source projects. A PHP library that pulls plain text out of old document formats — Word files, PDFs, PowerPoint slides, RTF, and more. Born in 2009 and finally given a proper v1.0.0 release in 2026.",
    starred: true,
    features: [
      "Extract text from PDF files",
      "Read old and new Word documents (.doc and .docx)",
      "Extract text from PowerPoint presentations",
      "Handle RTF and OpenDocument formats",
      "No extra software needed — pure PHP",
    ],
    techStack: ["PHP 8.3+"],
    status: "completed",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/TextAtAnyCost",
        icon: BiLogoGithub,
      },
    ],
  },
  {
    title: "Miette",
    description:
      "A lightweight Python library for reading old-style Word documents (.doc files). Extracts plain text with a simple, familiar interface. Revived in 2026 after more than a decade of quiet — fully rewritten for modern Python.",
    features: [
      "Read legacy Word .doc files",
      "Extract all plain text content",
      "Simple file-like API",
      "Minimal dependencies",
    ],
    techStack: ["Python 3.8+"],
    status: "alpha",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/Miette",
        icon: BiLogoGithub,
      },
    ],
  },
  {
    title: "cfb",
    description:
      "A Python library for reading the internal structure of old-style Microsoft Office files. The .doc, .xls, and .ppt formats are actually containers full of streams and folders — this library lets you open them and navigate what's inside. The foundation that Miette is built on.",
    features: [
      "Open and inspect old Office file containers",
      "Navigate internal folders and data streams",
      "File-like reading interface",
      "Handles malformed or unusual files gracefully",
    ],
    techStack: ["Python 3.8+"],
    status: "alpha",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/cfb",
        icon: BiLogoGithub,
      },
    ],
  },
  {
    title: "fit",
    description:
      "A Python library for reading and writing Garmin FIT files — the binary format used by fitness devices to record activities, workouts, and health data. Fully ported to modern Python and given a proper new release in 2026.",
    features: [
      "Read and write .fit activity files",
      "Supports all standard FIT message types",
      "Dynamic and composite bit-packed fields",
      "Plugin system for custom message and file types",
      "Context-manager API with stream support",
    ],
    techStack: ["Python 3.9+"],
    status: "active",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/fit",
        icon: BiLogoGithub,
      },
    ],
  },
];

function getStatusLabel(status: Project["status"]) {
  switch (status) {
    case "active":
      return "Active";
    case "completed":
      return "Completed";
    case "alpha":
      return "Alpha";
    case "beta":
      return "Beta";
  }
}

export default function Projects() {
  return (
    <section id="projects" className="projects">
      <div className="container">
        <div className="section-title">
          <h2>Projects</h2>
          <p>Hobby projects and side experiments</p>
        </div>

        <div className="projects-list">
          {projects.map((project) => (
            <article key={project.title} className="project-card">
              <div className="project-header">
                <h3>
                  {project.logo ? (
                    <img src={project.logo} alt="" className="project-logo" />
                  ) : null}
                  {project.title}
                  {project.starred ? (
                    <BiSolidStar
                      className="project-star"
                      title="Popular project"
                    />
                  ) : null}
                </h3>
                <span className={`project-status status-${project.status}`}>
                  {getStatusLabel(project.status)}
                </span>
              </div>

              <p className="project-description">{project.description}</p>

              <div className="project-features">
                <h4>
                  <BiCodeAlt /> Features
                </h4>
                <ul>
                  {project.features.map((feature) => (
                    <li key={feature}>{feature}</li>
                  ))}
                </ul>
              </div>

              <div className="project-tech">
                <h4>
                  <BiGlobe /> Tech Stack
                </h4>
                <div className="tech-tags">
                  {project.techStack.map((tech) => (
                    <span key={tech} className="tech-tag">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>

              {(project.links.length > 0 || project.packages) && (
                <div className="project-links">
                  {project.links.map(({ label, url, icon: Icon }) => (
                    <a
                      key={label}
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Icon /> {label}
                    </a>
                  ))}
                  {project.packages && (
                    <ul className="project-packages">
                      {project.packages.map(({ name, npmUrl, githubUrl }) => (
                        <li key={name}>
                          <code>{name}</code>
                          <span className="package-links">
                            <a
                              href={githubUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <BiLogoGithub /> GitHub
                            </a>
                            <a
                              href={npmUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <SiNpm /> npm
                            </a>
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </article>
          ))}
        </div>

        <div className="github-profile">
          <a
            href="https://github.com/rembish"
            target="_blank"
            rel="noopener noreferrer"
          >
            <BiLogoGithub /> More projects on GitHub
          </a>
        </div>
      </div>
    </section>
  );
}
