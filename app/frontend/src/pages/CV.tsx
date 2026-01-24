import { BiDownload, BiMap, BiPhone, BiEnvelope, BiLogoLinkedinSquare, BiLogoGithub, BiCode, BiSlideshow } from 'react-icons/bi'
import { Link } from 'react-router-dom'

export default function CV() {
  return (
    <section id="resume" className="resume">
      <div className="container">
        <div className="section-title">
          <h2>Curriculum Vitae</h2>
          <p>IT manager / Senior team leader / Python professional</p>
        </div>

        <div className="cv-grid">
          {/* Left Column */}
          <div className="cv-sidebar">
            <h3 className="resume-title">Contact</h3>
            <div className="resume-item">
              <p>
                <a className="btn-download" href="/alex-rembish-cv.pdf" download>
                  <BiDownload /> Download a <strong>PDF version</strong>
                </a>
              </p>
              <p><BiMap /> Wichterlova 2372/8, Prague 8, Czechia</p>
              <p><BiPhone /> <a href="tel:00420775054554">+420 775 054 554</a></p>
              <p><BiEnvelope /> <a href="mailto:alex@rembish.org">alex@rembish.org</a></p>
            </div>

            <h3 className="resume-title">Education</h3>
            <div className="resume-item">
              <h4>Bachelor of Applied Mathematics and Informatics</h4>
              <h5>2002 - 2008</h5>
              <p><em>Novosibirsk State Technical University, Novosibirsk, Russia</em></p>
            </div>

            <h3 className="resume-title">Skills</h3>
            <div className="resume-item">
              <ul>
                <li>Python expert</li>
                <li>Containerization</li>
                <li>Decreasing legacy code</li>
                <li>Code standardization</li>
                <li>Step-by-step refactoring</li>
                <li>Agile development</li>
                <li>Mentoring (up to Lead)</li>
                <li>Team coordination</li>
                <li>Public speaking</li>
                <li>Interviewing</li>
              </ul>
            </div>

            <h3 className="resume-title">Hard skills</h3>
            <div className="resume-item">
              <p>
                Python, PHP, C++, Javascript, Bash<br />
                Nginx, uwsgi, async frameworks<br />
                MySQL family databases<br />
                Linux (Debian, Ubuntu, Mint)<br />
                Cassandra, MongoDB and other NoSQL dbs<br />
                Docker, Kubernetes, Helm<br />
                Prometheus, Grafana, Kibana<br />
                Azkaban, Sentry, Jaeger<br />
                Virtualization (kvm, lxc, openvz)<br />
                CI/CD, bootstrapping and automation<br />
                Debian packaging<br />
                Python packaging<br />
                Coding standards<br />
                Complex automated testing<br />
                Code reviewing
              </p>
            </div>

            <h3 className="resume-title">Languages</h3>
            <div className="resume-item">
              <p>
                Russian | Native<br />
                Czech | Fluent<br />
                English | Professional working proficiency
              </p>
            </div>

            <h3 className="resume-title">Interests</h3>
            <div className="resume-item">
              <p>
                Travel<br />
                Drone piloting<br />
                Aerial photography<br />
                Indoor climbing
              </p>
            </div>

            <h3 className="resume-title">Public speaking</h3>
            <div className="resume-item">
              <h4>The way of a backend programmer</h4>
              <p>
                <a href="https://www.televizeseznam.cz/video/seznam-cz/aleksey-rembish-cesta-backend-programatora-63967281">Video</a>,{' '}
                <a href="http://slides.com/rembish/the-way-of-a-backend-programmer">Slides</a>
              </p>

              <h4>Super() quiz</h4>
              <p>
                <a href="https://www.youtube.com/watch?v=rmpuAJfJyos">Video</a>,{' '}
                <a href="http://slides.com/rembish/super-quiz-pyvo">Slides</a>
              </p>

              <h4>Bytecode manipulations</h4>
              <p>
                <a href="https://www.youtube.com/watch?v=LBFHzDfgfqg">Video</a>,{' '}
                <a href="http://slides.com/rembish/bytecode">Slides</a>
              </p>
            </div>

            <h3 className="resume-title">Links</h3>
            <div className="resume-item">
              <p><BiLogoLinkedinSquare /> <a href="https://www.linkedin.com/in/rembish/">linkedin.com/in/rembish</a></p>
              <p><BiLogoGithub /> <a href="https://github.com/rembish">github.com/rembish</a></p>
              <p><BiCode /> <a href="https://app.codesignal.com/profile/rembish">app.codesignal.com/profile/rembish</a></p>
              <p><BiSlideshow /> <a href="http://slides.com/rembish">slides.com/rembish</a></p>
            </div>
          </div>

          {/* Right Column */}
          <div className="cv-main">
            <h3 className="resume-title">Profile</h3>
            <div className="resume-item">
              <h4>Alex Rembish</h4>
              <p>
                I have more than 16 years of active programming experience including 9 years as a Python
                expert, 5+ years as a team leader and the last 3 years as the head of backend development.
              </p>
              <p>
                I'm now looking for a new opportunity with an interesting startup or an older project with
                a rich history and complex issues that need to be solved. Feel free to <Link to="/contact">contact me</Link> if you're
                interested in a technical leader, an architect, or a Python evangelist.
              </p>
              <p>CZ/EU citizen</p>
            </div>

            <h3 className="resume-title">Professional Experience</h3>

            <div className="resume-item">
              <h4>Head of Development</h4>
              <h5>Oct 2021 - Present</h5>
              <p><em><a href="https://shoptet.cz">Shoptet, a.s.</a> | Prague</em></p>
              <p>
                Managing 4 teams (20 programmers and tech leaders). Setting up better agile processes,
                improving relations with the Operations and QA departments, coordinating better product
                roadmap's planning.
              </p>
              <ul>
                <li>Changes to be explained</li>
                <li>Problems are to be solved, not to be hidden</li>
                <li>Simpler hiring process</li>
              </ul>
            </div>

            <div className="resume-item">
              <h4>Software Architect</h4>
              <h5>Jan 2021 - Sep 2021</h5>
              <p><em>Shoptet, a.s. | Prague</em></p>
              <p>
                Starting a new project with the external team of programmers. Setting up a complete
                project environment including automation, basic cloud infrastructure (dev side), and
                general support.
              </p>
              <ul>
                <li>Continuous Integration and delivery</li>
                <li>Kubernetes manifests</li>
                <li>Metrics and logging</li>
              </ul>
            </div>

            <div className="resume-item">
              <h4>Head of development</h4>
              <h5>Feb 2019 - Dec 2020</h5>
              <p><em><a href="https://seznam.cz">Seznam.cz a.s.</a> @ <a href="https://sklik.cz">Sklik.cz</a> | Prague</em></p>
              <p>
                Managing up to 18 teams (75 programmers and tech leaders) in 5 different locations in
                the Czech Republic. Coordinating technological roadmap and consulting product development
                estimates. Decreasing technical debt.
              </p>
              <ul>
                <li>Transparent development, building product vs dev relations</li>
                <li>Technological tasks are part of the department roadmap</li>
                <li>Problems are to be solved, not to be hidden</li>
                <li>Lead technical meetups</li>
                <li>Metrics, SLA/SLO</li>
                <li>Business logs to be streamed</li>
              </ul>
            </div>

            <div className="resume-item">
              <h4>Team leader</h4>
              <h5>May 2017 - Jan 2019</h5>
              <p><em>Seznam.cz a.s. @ Sklik.cz | Prague</em></p>
              <p>
                Leading two teams (10 programmers) in 2 different locations in the Czech Republic.
                Primarily responsible for developing and maintaining <a href="https://partner.seznam.cz">the partners' portal</a> at Sklik.cz.
                Mentoring less experienced colleagues (up to Senior). Public speaking about Python.
                Containerization of frontend components and other Python-based services.
              </p>
              <ul>
                <li>Team grew from 2 to 10 members</li>
                <li>Lead developer on two "first line" web applications at Sklik.cz</li>
                <li>Reduced on-boarding time from 2 days to 15 minutes</li>
                <li>Several core components were switched from a legacy to open-source codebase</li>
                <li>Python 2 to 3 migration</li>
                <li>Stable and well-documented scripts for partners' revenue calculations</li>
              </ul>
            </div>

            <div className="resume-item">
              <h4>Senior Python Programmer</h4>
              <h5>Jun 2014 - Apr 2017</h5>
              <p><em>Seznam.cz a.s. @ Sklik.cz | Prague</em></p>
              <p>
                As a separated programmer, I worked almost on all Sklik.cz components written in Python:
                libraries, websites, RPC servers and maintenance scripts.
              </p>
              <ul>
                <li>Changed own agenda from C++ back to Python to dive deeper and extend knowledge of the language</li>
                <li>Split a monolithic repository for core Sklik.cz websites into three separated websites for partners, advertisers and administrators</li>
                <li>Wrote a microframework (based on Flask) for step-by-step replacement of the old legacy code (based on <code>apache</code> + <code>mod_python</code>)</li>
                <li>Standardized a bunch of core modules written in Python (not only at Sklik.cz, but for whole Seznam infrastructure</li>
              </ul>
            </div>

            <div className="resume-item">
              <h4>C++ Programmer</h4>
              <h5>Feb 2013 - May 2014</h5>
              <p><em>Seznam.cz a.s. @ Sklik.cz | Prague</em></p>
              <p>
                Working in a smaller team developing servers for context advertisements'. Learned how
                to deal with large repositories and how to work on the same codebase with other
                programmers: coding standards, reviews, advanced versioning, packaging, project structure.
              </p>
              <ul>
                <li>Built an internal testing system for RPC servers based on Python's Unittest2 module (this system survived for 8 years)</li>
                <li>Worked on the first version of automatic adult content testing for the internal approval system</li>
              </ul>
            </div>

            <div className="resume-item">
              <h4>Senior Python Programmer</h4>
              <h5>Aug 2011 - Feb 2013</h5>
              <p><em><a href="https://www.glogster.com/personal">Glogster a.s.</a> | Prague</em></p>
              <p>
                Built <a href="https://edu.glogster.com">an education platform</a> based on Python and Cassandra (old codebase was completely
                rewritten). Completed OOP solution based on data models. Project cold-start. New features
                analysis and further implementation.
              </p>
            </div>

            <div className="resume-item">
              <h4>PHP Programmer</h4>
              <h5>Mar 2010 - Jul 2011</h5>
              <p><em><a href="https://www.wdf.cz/">Web Design Factory s.r.o.</a> | Prague</em></p>
              <p>
                High-load MySQL optimization, bottle-neck searching. Old PHP code improvement,
                implementation of new features. After half a year, new Glogster application architecture
                and code development. Switched from PHP to Python language.
              </p>
            </div>

            <div className="resume-item">
              <h4>C++ Programmer</h4>
              <h5>May 2005 - Aug 2008</h5>
              <p><em>First all-Siberian investment company "ICSI" | Novosibirsk</em></p>
              <p>
                Developing software for keeping customers' stock baskets and accounts. Supporting
                a previous version of an application. Intranet system administration and solving users'
                problems.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
