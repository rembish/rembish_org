# Changelog

## 0.10.1 (2026-01-24)

- Added birthplace and home markers on travel map

## 0.10.0 (2026-01-24)

- Added Travels page with interactive world map
- Travel statistics: UN countries (193), TCC destinations (330), NomadMania regions (1301)
- Map color gradient based on visit dates (older visits = lighter blue, 2010 baseline)
- Three tabs: Map view, UN Countries list, TCC Destinations list
- Microstate markers for small countries not visible on map
- Admin-only NomadMania regions XLSX upload with safe transaction handling
- Database migrations for travel tables, microstates, and NM regions
- Login/logout now returns to the current page instead of home
- Fixed map coloring for UAE, Vatican, Yemen, Somalia, and territory visits

## 0.9.6 (2026-01-24)

- Added Projects page with GitHub repositories (TextAtAnyCost, Miette, cfb, fit)
- Added shining star animation for popular projects
- Added GitHub profile link to Projects page
- Map on Contact page now centers on Prague with wider view
- Version number in footer linking to changelog page
- Changelog page with timeline-style layout

## 0.9.5 (2026-01-24)

- Added Cloudflare Turnstile CAPTCHA to contact form

## 0.9.4 (2026-01-24)

- Security hardening for production

## 0.9.3 (2026-01-24)

- Production deployment setup for GCP Cloud Run

## 0.9.2 (2026-01-24)

- Updated CV with current position (Pure Storage)
- Twitter icon updated to X

## 0.9.1 (2026-01-24)

- Google OAuth login for admin access
- Added vCard and PGP key links to contact page
- Keybase verification file exposed
- Fixed download button icon visibility on CV page
- Fixed navigation spacing for auth buttons
- Removed legacy Flask codebase (trips, drone flights, old templates)

## 0.9.0 (2026-01-24)

- New React frontend + FastAPI backend (rewrite in progress)
- CV page migrated with modernized styling
- Contact form with spam protection
- Switched from Google Maps to OpenStreetMap (Leaflet)

## 0.8.0 (2022-05-01)

- Address updated after moving

## 0.7.3 (2022-01-24)

- Dependency fixes

## 0.7.2 (2021-12-06)

- CV updated

## 0.7.1 (2021-01-06)

- Work contact email corrected

## 0.7.0 (2021-01-03)

- New job added: Shoptet
- Switched to Google Maps on contacts page

## 0.6.0 (2020-12-07)

- Address updated after moving
- Left Seznam

## 0.5.2 (2020-11-26)

- Drone flight log improvements (colors, private flights, MySQL backend)

## 0.5.1 (2020-11-24)

- Flight map and statistics added

## 0.5.0 (2020-11-23)

- Flight logging feature added
- Country flags support

## 0.4.0 (2020-10-26)

- User login/logout added
- MySQL database integration

## 0.3.0 (2020-10-21)

- CV page created (replaced Resume)
- Early work experience added

## 0.2.0 (2020-10-20)

- Contact form with Telegram notifications
- Changelog page added
- License added

## 0.1.0 (2020-10-19)

- Initial release: basic structure, containerization, CI/CD
