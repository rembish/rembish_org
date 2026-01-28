import {
  BiDownload,
  BiMap,
  BiPhone,
  BiEnvelope,
  BiLogoLinkedinSquare,
  BiLogoGithub,
  BiCode,
  BiSlideshow,
} from "react-icons/bi";
import { Link } from "react-router-dom";

export default function CV() {
  return (
    <section id="resume" className="resume">
      <div className="container">
        <div className="section-title">
          <h2>Curriculum Vitae</h2>
          <p>Software Engineer / Python Expert / Test Infrastructure</p>
        </div>

        <div className="cv-grid">
          {/* Left Column */}
          <div className="cv-sidebar">
            <h3 className="resume-title">Contact</h3>
            <div className="resume-item">
              <p>
                <a
                  className="btn-download"
                  href="/alex-rembish-cv.pdf"
                  download
                >
                  <BiDownload /> Download a <strong>PDF version</strong>
                </a>
              </p>
              <p>
                <BiMap /> Wichterlova 2372/8, Prague 8, Czechia
              </p>
              <p>
                <BiPhone /> <a href="tel:00420775054554">+420 775 054 554</a>
              </p>
              <p>
                <BiEnvelope />{" "}
                <a href="mailto:alex@rembish.org">alex@rembish.org</a>
              </p>
            </div>

            <h3 className="resume-title">Education</h3>
            <div className="resume-item">
              <h4>Bachelor of Applied Mathematics and Informatics</h4>
              <h5>2002 - 2008</h5>
              <p>
                <em>
                  Novosibirsk State Technical University, Novosibirsk, Russia
                </em>
              </p>
            </div>

            <h3 className="resume-title">Skills</h3>
            <div className="resume-item">
              <ul>
                <li>Python expert</li>
                <li>Containerization</li>
                <li>Reducing legacy code</li>
                <li>Code standardization</li>
                <li>Step-by-step refactoring</li>
                <li>Agile development</li>
                <li>Mentoring (up to Lead)</li>
                <li>Team coordination</li>
                <li>Public speaking</li>
                <li>Interviewing</li>
              </ul>
            </div>

            <h3 className="resume-title">Hard Skills</h3>
            <div className="resume-item">
              <p>
                Python, JavaScript, Bash
                <br />
                MySQL, Cassandra, MongoDB
                <br />
                Docker, Kubernetes, Helm
                <br />
                GitHub Actions, GitLab CI
                <br />
                Prometheus, Grafana, Kibana
                <br />
                Sentry, Jaeger
                <br />
                Nginx, async frameworks
                <br />
                AI tools (Claude, Augment, ChatGPT)
                <br />
                Test automation
                <br />
                Python packaging
              </p>
            </div>

            <h3 className="resume-title">Languages</h3>
            <div className="resume-item">
              <p>
                Russian | Native
                <br />
                Czech | Fluent
                <br />
                English | Fluent
              </p>
            </div>

            <h3 className="resume-title">Interests</h3>
            <div className="resume-item">
              <p>
                Travel
                <br />
                Drone piloting
                <br />
                Aerial photography
                <br />
                Indoor climbing
                <br />
                Cosplay
              </p>
            </div>

            <h3 className="resume-title print-break-before">Public Speaking</h3>
            <div className="resume-item">
              <h4>The way of a backend programmer</h4>
              <p>
                <a href="https://www.televizeseznam.cz/video/seznam-cz/aleksey-rembish-cesta-backend-programatora-63967281">
                  Video
                </a>
                ,{" "}
                <a href="http://slides.com/rembish/the-way-of-a-backend-programmer">
                  Slides
                </a>
              </p>

              <h4>Super() quiz</h4>
              <p>
                <a href="https://www.youtube.com/watch?v=rmpuAJfJyos">Video</a>,{" "}
                <a href="http://slides.com/rembish/super-quiz-pyvo">Slides</a>
              </p>

              <h4>Bytecode manipulations</h4>
              <p>
                <a href="https://www.youtube.com/watch?v=LBFHzDfgfqg">Video</a>,{" "}
                <a href="http://slides.com/rembish/bytecode">Slides</a>
              </p>
            </div>

            <h3 className="resume-title">Links</h3>
            <div className="resume-item">
              <p>
                <BiLogoLinkedinSquare />{" "}
                <a href="https://www.linkedin.com/in/rembish/">
                  linkedin.com/in/rembish
                </a>
              </p>
              <p>
                <BiLogoGithub />{" "}
                <a href="https://github.com/rembish">github.com/rembish</a>
              </p>
              <p>
                <BiCode />{" "}
                <a href="https://app.codesignal.com/profile/rembish">
                  app.codesignal.com/profile/rembish
                </a>
              </p>
              <p>
                <BiSlideshow />{" "}
                <a href="http://slides.com/rembish">slides.com/rembish</a>
              </p>
            </div>
          </div>

          {/* Right Column */}
          <div className="cv-main">
            <h3 className="resume-title">Profile</h3>
            <div className="resume-item">
              <h4>Alex Rembish</h4>
              <p>
                Programming since 2005 with deep expertise in Python, including
                leadership roles spanning team lead to head of development.
                Currently focused on test infrastructure, Python modernization,
                and performance testing at enterprise scale.
              </p>
              <p>
                Passionate about code quality, automation, and solving complex
                technical challenges. Feel free to{" "}
                <Link to="/contact">contact me</Link> for collaboration or
                consulting opportunities.
              </p>
              <p>CZ/EU citizen</p>
            </div>

            <h3 className="resume-title">Professional Experience</h3>

            <div className="resume-item">
              <h4>Member of Technical Staff-5</h4>
              <h5>Feb 2023 - Present</h5>
              <p>
                <em>
                  <a href="https://www.purestorage.com">Pure Storage</a> |
                  Prague
                </em>
              </p>
              <p>
                Part of the devtest team building and maintaining test
                infrastructure for FlashArray and FlashBlade storage systems.
                Driving Python modernization efforts across the codebase
                including migrations, linting standardization, and performance
                testing frameworks.
              </p>
              <ul>
                <li>
                  Main contributor to "Workloads as Code" — internal performance
                  testing framework
                </li>
                <li>Python codebase modernization and linting improvements</li>
                <li>
                  Test infrastructure development for enterprise storage
                  products
                </li>
              </ul>
            </div>

            <div className="resume-item">
              <h4>Head of Development</h4>
              <h5>Oct 2021 - Sep 2022</h5>
              <p>
                <em>
                  <a href="https://shoptet.cz">Shoptet, a.s.</a> | Prague
                </em>
              </p>
              <p>
                Managed 4 teams (20 programmers and tech leaders). Improved
                agile processes, strengthened relations with Operations and QA
                departments, and coordinated product roadmap planning.
              </p>
              <ul>
                <li>Promoted transparency in technical decisions</li>
                <li>Fostered problem-solving culture over blame avoidance</li>
                <li>Streamlined the hiring process</li>
              </ul>
            </div>

            <div className="resume-item">
              <h4>Software Architect</h4>
              <h5>Jan 2021 - Sep 2021</h5>
              <p>
                <em>Shoptet, a.s. | Prague</em>
              </p>
              <p>
                Started a new project with an external development team. Set up
                a complete project environment including automation, basic cloud
                infrastructure (dev side), and ongoing support.
              </p>
              <ul>
                <li>Continuous Integration and delivery</li>
                <li>Kubernetes manifests</li>
                <li>Metrics and logging</li>
              </ul>
            </div>

            <div className="resume-item">
              <h4>Head of Development</h4>
              <h5>Feb 2019 - Dec 2020</h5>
              <p>
                <em>
                  <a href="https://seznam.cz">Seznam.cz a.s.</a> @{" "}
                  <a href="https://sklik.cz">Sklik.cz</a> | Prague
                </em>
              </p>
              <p>
                Managed up to 18 teams (75 programmers and tech leaders) in 5
                locations across the Czech Republic. Coordinated technological
                roadmap and consulted on product development estimates. Reduced
                technical debt.
              </p>
              <ul>
                <li>Built transparent product-development relationships</li>
                <li>
                  Integrated technical initiatives into department roadmap
                </li>
                <li>Cultivated a culture of open problem-solving</li>
                <li>Led technical meetups</li>
                <li>Established metrics and SLA/SLO standards</li>
                <li>Implemented business log streaming</li>
              </ul>
            </div>

            <div className="resume-item print-break-before">
              <h4>Team Leader</h4>
              <h5>May 2017 - Jan 2019</h5>
              <p>
                <em>Seznam.cz a.s. @ Sklik.cz | Prague</em>
              </p>
              <p>
                Led two teams (10 programmers) in 2 locations across the Czech
                Republic. Primarily responsible for developing and maintaining{" "}
                <a href="https://partner.seznam.cz">the partners' portal</a> at
                Sklik.cz. Mentored junior colleagues up to Senior level. Gave
                public talks about Python. Containerized frontend components and
                other Python-based services.
              </p>
              <ul>
                <li>Team grew from 2 to 10 members</li>
                <li>
                  Lead developer on two "first line" web applications at
                  Sklik.cz
                </li>
                <li>Reduced onboarding time from 2 days to 15 minutes</li>
                <li>
                  Several core components were switched from a legacy to
                  open-source codebase
                </li>
                <li>Python 2 to 3 migration</li>
                <li>
                  Stable and well-documented scripts for partners' revenue
                  calculations
                </li>
              </ul>
            </div>

            <div className="resume-item">
              <h4>Senior Python Programmer</h4>
              <h5>Jun 2014 - Apr 2017</h5>
              <p>
                <em>Seznam.cz a.s. @ Sklik.cz | Prague</em>
              </p>
              <p>
                As an individual contributor, I worked on almost all Sklik.cz
                components written in Python: libraries, websites, RPC servers,
                and maintenance scripts.
              </p>
              <ul>
                <li>
                  Changed own agenda from C++ back to Python to dive deeper and
                  extend knowledge of the language
                </li>
                <li>
                  Split a monolithic repository for core Sklik.cz websites into
                  three separate websites for partners, advertisers, and
                  administrators
                </li>
                <li>
                  Wrote a microframework (based on Flask) for step-by-step
                  replacement of the old legacy code (based on{" "}
                  <code>apache</code> + <code>mod_python</code>)
                </li>
                <li>
                  Standardized core Python modules across Sklik.cz and the
                  broader Seznam infrastructure
                </li>
              </ul>
            </div>

            <div className="resume-item">
              <h4>C++ Programmer</h4>
              <h5>Feb 2013 - May 2014</h5>
              <p>
                <em>Seznam.cz a.s. @ Sklik.cz | Prague</em>
              </p>
              <p>
                Worked in a small team developing servers for contextual
                advertising. Learned how to deal with large repositories and
                collaborate on shared codebases: coding standards, reviews,
                advanced versioning, packaging, and project structure.
              </p>
              <ul>
                <li>
                  Built an internal testing system for RPC servers based on
                  Python's Unittest2 module (this system survived for 8 years)
                </li>
                <li>
                  Worked on the first version of automatic adult content testing
                  for the internal approval system
                </li>
              </ul>
            </div>

            <div className="resume-item">
              <h4>Senior Python Programmer</h4>
              <h5>Aug 2011 - Feb 2013</h5>
              <p>
                <em>
                  <a href="https://www.glogster.com/personal">Glogster a.s.</a>{" "}
                  | Prague
                </em>
              </p>
              <p>
                Built{" "}
                <a href="https://edu.glogster.com">an education platform</a>{" "}
                from scratch using Python and Cassandra, completely rewriting
                the old codebase. Designed an OOP architecture based on data
                models. Analyzed and implemented new features.
              </p>
            </div>

            <div className="resume-item">
              <h4>PHP Programmer</h4>
              <h5>Mar 2010 - Jul 2011</h5>
              <p>
                <em>
                  <a href="https://www.wdf.cz/">Web Design Factory s.r.o.</a> |
                  Prague
                </em>
              </p>
              <p>
                Optimized high-load MySQL databases and identified performance
                bottlenecks. Improved legacy PHP code and implemented new
                features. After six months, led the architecture and development
                of a new Glogster application. Transitioned from PHP to Python.
              </p>
            </div>

            <div className="resume-item">
              <h4>C++ Programmer</h4>
              <h5>May 2005 - Aug 2008</h5>
              <p>
                <em>
                  First all-Siberian investment company "ICSI" | Novosibirsk
                </em>
              </p>
              <p>
                Developed software for managing customers' stock portfolios and
                accounts. Maintained legacy applications. Administered intranet
                systems and provided user support.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
