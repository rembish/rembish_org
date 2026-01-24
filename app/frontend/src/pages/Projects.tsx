import { BiGlobe, BiCodeAlt, BiLinkExternal, BiLogoGithub, BiSolidStar } from 'react-icons/bi'

interface Project {
  title: string
  description: string
  logo?: string
  starred?: boolean
  features: string[]
  techStack: string[]
  status: 'active' | 'completed' | 'alpha'
  links: { label: string; url: string; icon: React.ComponentType }[]
}

const projects: Project[] = [
  {
    title: 'rembish.org',
    description:
      'This very website! A personal portfolio and contact page built from scratch with modern web technologies and AI assistance.',
    features: [
      'Interactive map with Leaflet',
      'Type animation effects',
      'Contact form with Cloudflare Turnstile',
      'Google OAuth authentication',
      'Fully responsive design',
      'Built entirely with Claude AI',
    ],
    techStack: [
      'React',
      'TypeScript',
      'Vite',
      'FastAPI',
      'SQLAlchemy',
      'Google Cloud',
    ],
    status: 'active',
    links: [
      { label: 'Website', url: 'https://rembish.org', icon: BiLinkExternal },
      { label: 'GitHub', url: 'https://github.com/rembish/rembish_org', icon: BiLogoGithub },
    ],
  },
  {
    title: 'Am I Free?',
    description:
      'A web application that helps you plan your vacation days by calculating working days spent on trips, excluding weekends and public holidays automatically.',
    logo: '/amifree-logo.svg',
    features: [
      'Calculate vacation days needed for trips',
      'Exclude weekends and public holidays automatically',
      'Track multiple trips throughout the year',
      'View remaining vacation days',
      'What-if calculator for planning future trips',
      'Support for multiple countries',
    ],
    techStack: [
      'React',
      'TypeScript',
      'Vite',
      'Mantine UI',
      'FastAPI',
      'SQLAlchemy',
      'MySQL',
      'Google Cloud',
    ],
    status: 'alpha',
    links: [
      { label: 'Website', url: 'https://amifree.info', icon: BiLinkExternal },
    ],
  },
  {
    title: 'TextAtAnyCost',
    description:
      'PHP scripts to read text content from different binary formats: PDF, DOC, PPT, RTF and more. One of my oldest and most popular open source projects.',
    starred: true,
    features: [
      'Extract text from PDF files',
      'Read Microsoft Word documents',
      'Parse PowerPoint presentations',
      'Handle RTF files',
      'Simple API for text extraction',
    ],
    techStack: ['PHP'],
    status: 'completed',
    links: [
      { label: 'GitHub', url: 'https://github.com/rembish/TextAtAnyCost', icon: BiLogoGithub },
    ],
  },
  {
    title: 'Miette',
    description:
      'A lightweight Microsoft Office documents reader for Python. Provides easy access to content in Office file formats.',
    features: [
      'Read Microsoft Office documents',
      'Lightweight and fast',
      'Simple Python API',
      'No heavy dependencies',
    ],
    techStack: ['Python'],
    status: 'completed',
    links: [
      { label: 'GitHub', url: 'https://github.com/rembish/Miette', icon: BiLogoGithub },
    ],
  },
  {
    title: 'cfb',
    description:
      'Python library for reading and writing Microsoft Compound File Binary (CFB) format. The underlying format used by older Office documents.',
    features: [
      'Read CFB files',
      'Write CFB files',
      'Python file-like IO interface',
      'Low-level access to compound file structures',
    ],
    techStack: ['Python'],
    status: 'completed',
    links: [
      { label: 'GitHub', url: 'https://github.com/rembish/cfb', icon: BiLogoGithub },
    ],
  },
  {
    title: 'fit',
    description:
      'Python SDK for working with FIT (Flexible and Interoperable Data Transfer) files. FIT is used by fitness devices like Garmin for activity data.',
    features: [
      'Parse FIT files',
      'Access workout and activity data',
      'Support for various FIT message types',
      'Pythonic API',
    ],
    techStack: ['Python'],
    status: 'completed',
    links: [
      { label: 'GitHub', url: 'https://github.com/rembish/fit', icon: BiLogoGithub },
    ],
  },
]

function getStatusLabel(status: Project['status']) {
  switch (status) {
    case 'active':
      return 'Active'
    case 'completed':
      return 'Completed'
    case 'alpha':
      return 'Alpha'
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
                    <BiSolidStar className="project-star" title="Popular project" />
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
                    <a key={label} href={url} target="_blank" rel="noopener noreferrer">
                      <Icon /> {label}
                    </a>
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>

        <div className="github-profile">
          <a href="https://github.com/rembish" target="_blank" rel="noopener noreferrer">
            <BiLogoGithub /> More projects on GitHub
          </a>
        </div>
      </div>
    </section>
  )
}
