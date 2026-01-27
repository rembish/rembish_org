# Changelog

## 0.13.1 (2026-01-27)

### Location Widget
- Location button now shows city name with country flag
- Logged-in users see admin's avatar with "in [city] [flag]" and hover tooltip
- Anonymous visitors don't see the location widget

### Travels Map
- Added current location marker showing admin's avatar
- Marker only visible to logged-in users
- Shows "Now: [city]" on hover

### Contact Form
- Form prefills name and email for logged-in users

### Trip Calendar (Admin)
- Czech holidays shown as red background on calendar dates
- Birthday icon (cake) on trip days overlapping someone's birthday
- Destination holiday icon (party) on future trip days matching destination country holidays
- Holiday icons also shown in table view for future trips

## 0.13.0 (2026-01-27)

### Close Ones (Admin)
- New "Close Ones" tab in admin panel to manage family/friends
- Add users by email - they remain "Pending" until first Google login
- User cards show avatar, name, email, birthday, status, and trip count
- Edit user details including birthday (date picker with dd.mm.yyyy format)
- Remove users with confirmation dialog
- Login now requires email to be pre-registered in the system

### User Activation Flow
- New users are created as "Pending" (inactive)
- First Google login activates the account and syncs profile picture
- Unregistered emails are denied login access

## 0.12.3 (2026-01-26)

### Future Trips Handling
- Future trips are now excluded from all travel statistics (map, UN countries, TCC destinations)
- Stats page shows future trips for logged-in users with purple bar color
- Mixed months (completed + planned trips) display blue-to-purple gradient bars
- Admin page marks future trips with purple styling and ⏳ badge

### UI Improvements
- Added (+N) planned count badges to UN/TCC stat widgets with "In plans" tooltip
- Added planned trips count badge to Trips stat widget
- Changed stat format from "/X" to "of X" (e.g., "45 of 193" instead of "45/193")
- TCC destination input now auto-focuses after selection
- Fixed date picker selecting wrong day (timezone issue with UTC parsing)

## 0.12.2 (2026-01-26)

### Travels Map
- Added color legend in top-right corner with gradient scales for visit frequency and recency
- Territory names now show parent country (e.g., Greenland shows "Denmark")
- Merged map polygons: Western Sahara into Morocco, Somaliland into Somalia, Northern Cyprus into Cyprus
- Fixed Palestine not coloring on map (missing map_region_code)

### UN Countries & TCC Destinations Pages
- Applied same gradient color scheme as map (hue by visit count, lightness by recency)
- Added visit count badges next to country/destination names
- Added region/continent statistics showing visited/total with percentage
- Added "Visited only" toggle filter (synced between pages, stored in localStorage)
- Added color legend with date type note (last visit for UN, first visit for TCC)
- UN page now shows last visit date instead of first visit

### Stats Page
- Changed flag tooltip from "(new)" to "(first visit)" for first-time country visits

## 0.12.0 (2026-01-25)

### Trip Management (Admin)
- Add/Edit/Delete trips via modal form in admin panel
- Date range picker with Monday as week start
- TCC destination selector with search (collapsed by default, auto-clears on select)
- City search with Nominatim geocoding and local caching
- Participant selection with "Other" count for unnamed companions
- Partial city visits (click to toggle, displayed in grey)
- First-visit tracking automatically updates when trips are added/edited/deleted

### City Search
- Local database search with country code filtering
- Nominatim fallback with 400ms debounce and 1s rate limiting
- Country flags displayed next to search results
- Results cached to local database for faster future searches
- Structured search with country name parameter for accurate results

### Data Integrity
- Visit dates correctly cleared when all trips to a destination are deleted
- Duplicate city prevention (checks by name + country_code)
- City data cleanup: removed entries without country codes
- Fixed country/code mismatches (Oslo, Katowice)

### Migrations
- 019: Add country_code field to cities table
- 020: Backfill country_code for existing cities from UN countries and territory mappings

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
