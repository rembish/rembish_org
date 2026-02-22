import {
  BiGlobe,
  BiCodeAlt,
  BiLinkExternal,
  BiLogoGithub,
  BiSolidStar,
} from "react-icons/bi";

interface Project {
  title: string;
  description: string;
  logo?: string;
  starred?: boolean;
  features: string[];
  techStack: string[];
  status: "active" | "completed" | "alpha";
  links: { label: string; url: string; icon: React.ComponentType }[];
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
    title: "TCC TopoJSON",
    description:
      "An open-source TopoJSON world map with 330 polygons matching the Travelers' Century Club destination list. Nothing like this existed before — NomadMania's regions are proprietary, TCC has no polygon data, and existing world atlases only cover countries. Built from Natural Earth 10m shapefiles with transcontinental splits, island extractions, and Antarctic claim sectors.",
    features: [
      "330 TCC destinations as individual polygons",
      "Transcontinental splits (Russia, Turkey, Egypt at precise boundaries)",
      "All 7 UAE emirates, Indonesian island groups, disputed territories",
      "Antarctic claim wedges and remote island extractions",
      "Available via npm or jsDelivr CDN",
    ],
    techStack: ["Python", "Shapely", "GeoPandas", "mapshaper", "TopoJSON"],
    status: "active",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/tcc-topojson",
        icon: BiLogoGithub,
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

              {project.links.length > 0 && (
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
