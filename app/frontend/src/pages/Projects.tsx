import { useNavigate, useParams } from "react-router-dom";
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

type TabType = "web" | "modules";

const webProjects: Project[] = [
  {
    title: "rembish.org",
    description:
      "This very website! What started as a simple portfolio page grew into a full personal travel and life management platform — trip planning, flight and drone tracking, encrypted vault, photo galleries, meme feed, and more. Built entirely with Claude AI.",
    starred: true,
    features: [
      "Interactive travel map with 193 UN countries, 330 TCC, and 265 NM UN+ destinations",
      "Drone flights — Telegram bot upload, geocoded locations, battery telemetry, anomaly detection",
      "Flight tracking with AeroDataBox lookup, statistics, and Flighty import",
      "Encrypted vault for passports, visas, travel documents, loyalty programs, and vaccinations",
      "Photo galleries — Instagram albums, cosplay gallery, and country-based world map",
      "Trip planner with TripClimate integration, travel advisories, and vacation balance",
      "Meme feed — Telegram capture with AI triage via Claude Haiku",
      "iOS app API — Bearer token auth with direct drone flight and meme upload endpoints",
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
    title: "TripClimate",
    description:
      "A travel planning tool that shows what awaits before you book. Layers cultural events, sporting events, public holidays, weather, seasonality, visa requirements, and travel warnings into an interactive calendar. Includes a world map, destination Compass, browsable Event Guide, and personalized settings for units and passport country. Covers 250+ countries.",
    starred: true,
    features: [
      "423 curated festivals across 167 countries: Ramadan, Carnival, Songkran, Holi, Nyepi, Oktoberfest, and more",
      "194 sporting events: F1, Grand Slams, marathons, Olympics, cycling tours",
      "Public holidays for 249 countries with 3-tier resolution fallback",
      "Historical weather averages, extreme condition alerts, closed seasons, and seasonality indicators",
      "Visa requirements — personalized by passport country with GeoIP-based detection",
      "Travel advisories from US State Dept, Canada, UK FCDO, and Germany",
      "Travel Score — Explorer/Chill modes to surface trips that match your style",
      "Compass — destination ranking by month, weather preference, and travel vibe",
      "Event Guide — browsable directory of 1,490 festivals, sports events, and holidays with descriptions and photos",
      "World choropleth map with zoom/pan, multiple view modes, and biome overlays",
      "User preferences: temperature/precipitation units and passport country, persisted locally",
    ],
    techStack: ["Python 3.12+", "FastAPI", "Alpine.js", "Google Cloud Run"],
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
];

const moduleProjects: Project[] = [
  {
    title: "pydjirecord",
    description:
      "A Python 3.10+ parser for DJI drone flight log files (.txt binary format). Handles format versions 1–14 with XOR and AES-256-CBC decryption. Built as a rewrite of the Rust dji-log-parser, with improvements: zero-coordinate backfill from OSD GPS frames, accurate video/photo/distance stats from raw telemetry, and local keychain caching for the DJI API.",
    starred: true,
    features: [
      "Parse DJI flight logs across format versions 1–14",
      "XOR + AES-256-CBC decryption with DJI API keychain fetching",
      "Multiple output formats: JSON, GeoJSON, KML, CSV, hardware report",
      "Zero-coordinate backfill from OSD GPS telemetry frames",
      "Accurate photo count, video time, and distance from raw records",
      "Flight anomaly detection with RED/AMBER/GREEN severity levels",
    ],
    techStack: ["Python 3.10+", "PyCryptodome", "httpx"],
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
    title: "xcodeproj-creator",
    description:
      "A Python library and CLI tool that generates Xcode .xcodeproj bundles from scratch — on Linux or any platform, no macOS required. Ideal for CI/CD pipelines and cross-platform build automation where you need to programmatically produce valid Xcode projects for iOS and macOS apps.",
    starred: true,
    features: [
      "Generate full Xcode projects on Linux or any non-macOS platform",
      "Supports object model v56 (all Xcode versions) and v77 (Xcode 16+ with filesystem-sync groups)",
      "Multiple product types: iOS App, Framework, Static Library, Unit Tests, UI Tests, App Extensions",
      "Configurable build settings, deployment targets, Swift versions, and team IDs",
      "Shell script build phases, asset catalogs, and resource management",
      "Both Python API and CLI (xcodeproj-create command)",
    ],
    techStack: ["Python 3.12+"],
    status: "beta",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/xcodeproj-creator",
        icon: BiLogoGithub,
      },
      {
        label: "PyPI",
        url: "https://pypi.org/project/xcodeproj-creator/",
        icon: SiPypi,
      },
    ],
  },
  {
    title: "TopoJSON Maps",
    description:
      "Three open-source TopoJSON world maps built from Natural Earth 10m shapefiles — one for each major travel tracking system, plus a standard ISO baseline. All published on npm and available via CDN.",
    starred: true,
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
      {
        label: "PyPI",
        url: "https://pypi.org/project/fit/",
        icon: SiPypi,
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
    status: "beta",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/cfb",
        icon: BiLogoGithub,
      },
      {
        label: "PyPI",
        url: "https://pypi.org/project/cfb/",
        icon: SiPypi,
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
      {
        label: "PyPI",
        url: "https://pypi.org/project/miette/",
        icon: SiPypi,
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
  const { tab } = useParams<{ tab?: string }>();
  const navigate = useNavigate();

  const activeTab: TabType = tab === "modules" ? "modules" : "web";
  const projects = activeTab === "web" ? webProjects : moduleProjects;

  return (
    <section id="projects" className="projects">
      <div className="container">
        <div className="section-title">
          <h2>Projects</h2>
          <p>Hobby projects and side experiments</p>
        </div>

        <div className="travel-tabs">
          <button
            className={`travel-tab ${activeTab === "web" ? "active" : ""}`}
            onClick={() => navigate("/projects/web")}
          >
            <BiGlobe /> Web
          </button>
          <button
            className={`travel-tab ${activeTab === "modules" ? "active" : ""}`}
            onClick={() => navigate("/projects/modules")}
          >
            <BiCodeAlt /> Modules
          </button>
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
