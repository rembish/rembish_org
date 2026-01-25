# Changelog

## 0.11.1 (2026-01-25)

### Data Seeding
- Production data migration with 219 trips, 1388 cities, 125 visits
- Trip participants linked to companion users (displayed with avatars in admin)

### City Data Cleanup
- Deduplicated 7 duplicate city entries
- Fixed country assignments: Berlin, Munich (Germany), Central Asian cities (Uzbekistan, Kazakhstan, Tajikistan), West African cities (Senegal, Mauritania)
- Fixed UTF-8 diacritics: Plzeň, Špindlerův Mlýn, Kraków, Žilina, Kołobrzeg, etc.

## 0.11.0 (2026-01-25)

### Territory Flags
- 68 TCC territories now display their own flags instead of parent country flags
- British overseas territories: Anguilla, Bermuda, British Virgin Islands, Cayman Islands, Falkland Islands, Gibraltar, Montserrat, Pitcairn, St. Helena, Ascension, Tristan da Cunha, Turks and Caicos, British Indian Ocean Territory
- US territories: Puerto Rico, US Virgin Islands, Guam, Northern Marianas, American Samoa
- French territories: French Polynesia, New Caledonia, Martinique, Guadeloupe, French Guiana, Reunion, Mayotte, St. Barthélemy, St. Martin, St. Pierre and Miquelon, Wallis and Futuna
- Dutch territories: Aruba, Curaçao, Sint Maarten, Bonaire
- UK nations: England, Scotland, Wales, Northern Ireland (with their own flags)
- Other: Faroe Islands, Hong Kong, Macau, Taiwan, Crown Dependencies (Jersey, Guernsey, Isle of Man)
- Custom flags for Somaliland and Northern Cyprus from Wikipedia Commons
- SVG flags from lipis/flag-icons (MIT license)

### Life Events
- Trip types: regular, work, relocation (replaces is_work_trip boolean)
- Birthday marker (May 1985, Novosibirsk) shown at end of stats timeline
- Relocation events marked with 📦 icon in stats
- Special background highlighting for life event months

### Stats Page Improvements
- Months now display newest to oldest (matching year order)
- Flag deduplication when visiting country and its dependency in same month

### Fixes
- Fixed version-sync corrupting pyproject.toml Python version settings

## 0.10.3 (2026-01-25)

- Travel map loads progressively: map appears immediately, tab data loads in background
- Split travel API into three endpoints for faster initial load
- Version sync now validates VERSION file format before updating

## 0.10.2 (2026-01-24)

- Added development tooling: linting, formatting, type checking
- CI pipeline blocks deployment if code quality checks fail
- Version management: `make version`, `make version-check`, `make version-sync`
- CI verifies git tag matches code versions before deployment

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
