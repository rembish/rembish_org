# Changelog

## 0.38.1 (2026-02-22)

### License Change
- Switched from CC BY-NC-ND 4.0 to GNU Affero General Public License v3.0 (AGPL-3.0)

### README Rewrite
- Updated README to reflect current project scope: travel management platform with 6 public pages, 10+ admin features, AI document extraction, encrypted vault, and role-based access

### Code Quality
- Split TripFormPage.tsx (5,303 lines) into 10 focused modules + 304-line orchestrator
  - `components/trip/`: types, helpers, EditTab, InfoTab, TransportTab, StaysTab, FlightModal, CarRentalModal, TransportBookingModal, AccommodationModal
  - Each tab fetches its own data, manages own vault state
  - No behavioral changes — pure refactor

## 0.38.0 (2026-02-21)

### Accommodation Bookings — "Stays" Tab
- New "Stays" tab on trip pages for hotel/apartment bookings
- Upload a booking confirmation (PDF or photo) and Claude Haiku auto-extracts property name, platform, dates, address, amount, payment status, guests, rooms, and confirmation code
- Platform detection: Booking.com, Agoda, Airbnb, direct, or other
- Payment status badges: paid (green), pay at property (orange), pay by date (red)
- Confirmation codes stored encrypted (AES-256-GCM), displayed only when vault is unlocked
- Attach/view/delete booking documents, edit and delete accommodations
- Clickable addresses open in Google Maps, booking URLs open in new tab

## 0.37.2 (2026-02-21)

### Fixers
- Search now matches country names (e.g. typing "Kenya" finds fixers with code KE)

## 0.37.1 (2026-02-21)

### Trip Info — Country Flag Tabs
- Multi-country trips now show a flag sidebar to switch between countries one at a time
- Desktop: vertical flag tabs on the left, mobile: horizontal flag bar on top
- Single-country trips render unchanged (no sidebar)

## 0.37.0 (2026-02-21)

### Transport Tab — Modal Refactor
- Transport tab now shows clean card lists only — all add/edit workflows moved into modals
- "Add Flight" modal: upload ticket (AI extraction), lookup by flight number (AeroDataBox), or manual entry — all in one modal with section dividers
- "Add Car Rental" modal: upload reservation for AI extraction or enter manually, with "Use extracted data" button to pre-fill the form
- "Add Transport Booking" modal: same extraction-to-form pattern for trains, buses, and ferries
- "+ Add" buttons moved into section headers next to the count
- Driving flags reminder restyled as a compact warning box below rental cards
- Fixed missing styles for select dropdowns and checkboxes in modals

### Transport Bookings
- Multiple train/bus/ferry bookings per trip on the transport tab
- Upload a ticket (PDF or photo) and Claude Haiku auto-extracts operator, service number, stations, times, carriage, seat, and booking reference
- Manual entry form with type selector (train/bus/ferry)
- Edit bookings, attach/view/delete ticket documents
- Booking references stored encrypted in the vault (AES-256-GCM)
- Duplicate detection on extract
- Station names link to Google Maps

### Database
- Migration 056: `transport_bookings` table with encrypted booking reference and document storage

## 0.36.0 (2026-02-21)

### Car Rental Tracking
- Multiple car rentals per trip on the transport tab — same layout as flights
- Upload a rental confirmation (PDF or photo) and Claude Haiku auto-extracts company, car class, transmission, pickup/dropoff locations and times, price, and confirmation number
- Manual entry form for adding rentals without a document
- Edit rentals after the trip to record the actual car received (vs. the booked class)
- Confirmation numbers stored encrypted in the vault (AES-256-GCM), visible only when vault is unlocked
- Pickup and dropoff locations link to Google Maps
- Duplicate detection: re-uploading the same confirmation flags it as already added
- Reminder note on transport tab to update driving flags on the Travels page
- Removed legacy `rental_car` and `flights_count` fields from trip edit form (data migrated to new table)

### Database
- Migration 055: `car_rentals` table with encrypted confirmation number support

## 0.35.2 (2026-02-21)

### Open Graph Link Previews
- Links shared in Slack, Telegram, Twitter, iMessage now show rich previews with title, description, and image
- Dynamic previews for trip photo albums (destinations + date + cover photo) and country photo pages
- Static previews for Home, CV, Travels, Photo Gallery, Photos Map, and other pages
- Fallback OG tags in index.html for bots that slip past nginx detection

### Bug Fix
- Fixed Instagram photo fetch failing on production — non-root Docker container couldn't create `/app/data` directory
- Cursor file moved to `/tmp` (always writable), removed redundant local directory creation when using GCS storage

## 0.35.1 (2026-02-21)

### Improved Reliability
- External service failures (Instagram, Nominatim, weather, currency, flights) now log full error details instead of failing silently
- Easier to diagnose sync issues and API outages from Cloud Run logs

## 0.35.0 (2026-02-21)

### Fixer-to-Trip Integration
- Fixers now appear on trip info country cards — auto-assigned on first view based on matching countries
- After first view, fully manual: add (+) or remove (×) fixers per trip
- Assigned fixers shown as green badges with name, type, star rating, and WhatsApp link
- Available (unassigned) fixers shown as dashed grey badges for easy adding
- Clicking a fixer name navigates to People > Fixers

## 0.34.0 (2026-02-21)

### Fixers UX Overhaul
- Country selector: searchable dropdown with flag+name chips instead of manual ISO code entry
- Link management: icon-based buttons (Instagram, Facebook, TripAdvisor, etc.) replace dropdown menus — click to add, auto-focused URL input
- Added Facebook and NomadMania as standard link types
- Card badges show service-specific icons (or short names for TourHQ, GetYourGuide, NomadMania) instead of generic link text
- Country flags shown as pill badges alongside fixer type
- WhatsApp field promoted to primary position (before phone)
- Modal widened from 400px to 700px to accommodate new fields
- Notes displayed as plain text without icon

## 0.33.0 (2026-02-21)

### Read-Only Viewer Access
- New "viewer" role for sharing trip data with family — read-only access to trips, calendar, events, and transport
- Viewers see only the Trips tab with all mutation buttons hidden (no add, edit, or delete)
- Trip detail pages show Info and Transport tabs in read-only mode
- Admin user management now has a role dropdown (Admin / Viewer / None) instead of a simple toggle

### "View As" Preview
- Admins can preview exactly what a viewer sees by clicking the eye icon on a viewer user's card
- A banner at the top shows whose view is being simulated, with an Exit button to return to admin mode

## 0.32.1 (2026-02-21)

### Bug Fixes
- Fixed vault document "View" button not working on mobile browsers

## 0.32.0 (2026-02-20)

### People Tab
- New "People" tab merges Close Ones and Addresses into a single tab with sub-tabs
- Consistent sub-tab pattern matching Documents (IDs / Vaccinations / Visas)

### Address Autocomplete
- Type-ahead address search powered by Nominatim — no more filling in line1/city/state/postal_code manually
- Results formatted as proper postal addresses (street, postcode + city, country)
- Pick a result, tweak it if needed, save
- Addresses can optionally be linked to a close-one user (avatar shown on card)
- Search filter matches both name and address text

## 0.31.0 (2026-02-20)

### Flight Ticket Extraction
- Upload a flight ticket (PDF or photo) on the transport tab — AI extracts all flights automatically
- Supports multi-leg itineraries: each leg shown as a reviewable card
- Duplicate detection: flights matching existing date+airports highlighted, pre-deselected
- Encrypted PNR storage: booking references extracted and stored in vault (AES-256-GCM)
- PNR display respects vault lock — masked when locked, full code with copy button when unlocked

### Global Vault Toggle
- Lock/unlock icon in top-right corner of all admin pages — no more hunting for the button
- Locks and unlocks vault from any page; VaultTab and transport tab react instantly
- Removed per-page lock/unlock buttons (VaultTab toolbar, transport page hint link)
- VaultTab locked screen simplified — just points to the global icon

## 0.30.1 (2026-02-20)

### Bug Fixes
- Fixed deploy workflow blocked by transitive npm vulnerabilities (d3-color, esbuild, minimatch) with no available fix — audit threshold raised from `high` to `critical`
- Fixed potential 500 error when duplicate participant IDs sent in trip create/update payload — now silently deduped
- Fixed stale `requirements.lock` causing deploy failure (missing `cachetools`)

### CI/CD
- Added lockfile freshness guard — CI and deploy workflows now verify `requirements.lock` matches `pyproject.toml`
- Added `make lockfile-check` target (included in `make check`)

## 0.30.0 (2026-02-20)

### Security Hardening
- CSRF protection on all API mutations — custom header prevents cross-site form attacks
- POST-only logout — no longer exploitable via `<img src>` tags
- Stricter redirect URL validation in OAuth flow
- Backend health check now verifies database connectivity
- Production Docker image runs as non-root user
- All deploy secrets explicitly declared

### Improved Error Handling
- App-wide error boundary catches uncaught errors with recovery UI instead of white screen

### Code Quality
- Split three oversized modules into focused, maintainable files:
  - Backend: `vault.py` (1,419 lines → 6 files), `trips.py` (1,595 lines → 4 files)
  - Frontend: `Admin.tsx` (5,254 lines → 16 files in `components/admin/`)
- Warnings treated as errors in test suite — catches deprecation issues early

### Under the Hood
- Shared API helper reduces boilerplate across all frontend API calls
- Auth state shared via React Context (single fetch instead of per-component)
- Hand-rolled caches replaced with TTLCache for reliability
- Removed unused `requests` dependency (migrated to `httpx`)
- Added dependency vulnerability scanning to CI pipeline (and to deploy workflow)
- Reproducible backend builds via lockfile
- Dependabot configured for all package ecosystems
- `.env` files excluded from Docker build contexts

### Database
- Added missing uniqueness constraint on trip destinations
- Enforced one-passport-per-trip at database level
- Added audit timestamps to all vault tables
- Vault endpoints now validate trip existence and passport document type

## 0.29.2 (2026-02-19)

### Bug Fix
- Fixed 413 error when uploading large visa PDFs — nginx default 1MB body limit raised to 10MB

## 0.29.1 (2026-02-19)

### Bug Fix
- Fixed vault file signed URLs failing on Cloud Run (500 error) — compute engine credentials can't sign locally, now uses IAM signBlob API

## 0.29.0 (2026-02-19)

### Travel Documents & File Storage
- New "Travel Documents" section in vault: store e-visas, ETAs, ESTAs, LOIs, entry permits, travel insurance, vaccination certificates
- Private file storage: upload PDFs and images, served via short-lived signed URLs (no public access)
- AI-powered metadata extraction: upload a visa PDF and Claude Haiku auto-fills document type, country, validity dates, entry type, and notes
- Passport linkage: link each travel document to the passport it was issued against
  - AI extraction auto-detects passport number and matches it to stored passports
  - "Linked Passport" dropdown when creating/editing travel documents
- File attachments on existing vault cards: attach passport scans, ID card photos, yellow book pages to documents and vaccinations

### Trip Integration
- Travel documents shown on trip info tab per country: type badge, entry type, passport label, validity dates
- Expiry warning if document expires before or during trip
- Auto-suggest: valid travel documents for each destination country automatically appear on trip info
- Single-entry visa lifecycle: used visas from completed trips are skipped
- Passport filtering: when a passport is assigned to a trip, only visas linked to that passport are shown
- "No visa/travel document" banner with `+ Add` button — navigates directly to vault with country pre-filled

### Vault UX
- "Show expired" toggle on travel documents (hidden by default)
- Travel documents sorted by expiry date (earliest first, no-expiry at end)

### Database
- Migration 042: vault_travel_docs, vault_files, trip_travel_docs, trip_passports tables
- Migration 043: passport linkage (document_id FK) and used flag on travel docs

## 0.28.2 (2026-02-19)

### Bug Fix
- Fixed health requirements data missing from production — `data/` gitignore pattern was excluding `src/data/health_requirements.json` from commits

## 0.28.1 (2026-02-19)

### Bug Fix
- Fixed CSP violation for passport flag images in vault (replaced external flagcdn.com with local SVG flags)

## 0.28.0 (2026-02-19)

### Vault — Secure Document Storage
- New admin section for storing sensitive travel documents with AES-256-GCM encryption
- Requires Google re-authentication with 10-minute auto-lock for access
- **Documents**: Passports, ID cards, driver's licenses with masked numbers, expiry warnings, soft-delete
- **Loyalty Programs**: Airline/hotel programs grouped by alliance (Star Alliance, Oneworld, SkyTeam)
- **Vaccinations**: Personal vaccination records with expiry tracking and "Lifetime" badge
- Copy-to-clipboard for sensitive fields (document numbers, membership numbers, batch numbers)
- Per-user records (admin + family members)

### Health Requirements on Trip Info
- Country health data from CDC Travelers' Health (244 countries) shown on trip info tab
- Required vaccinations (red), recommended (orange), consider (gray)
- Your vaccination records cross-referenced — covered vaccines shown in green with checkmark
- Handles combined vaccines (e.g., "Hepatitis A+B" covers both A and B requirements)
- Malaria risk areas with prophylaxis and drug resistance info
- Other disease risk tags per country

## 0.27.3 (2026-02-18)

### Flight Statistics
- New "Flights" tab on Travels page with detailed analytics:
  - Flights by year (recent first)
  - Top airlines, airports (with flags), routes, and aircraft types
  - Aircraft grouped into families (A320 family, Boeing 737 family, etc.) with variant tooltips
  - Horizontal bar charts with per-section color coding
  - Outlier bars use color-to-hot gradient for dominant entries
- 6th stat card in carousel: total flights, airports, and airlines count
  - Future flights shown as "+X planned"
- Stat cards grid changed from 5 to 3 columns (cleaner 3×2 layout)

### Flights Map
- Airport markers scaled by flight frequency (1–15+ flights)
- Country fill changed from orange to sky blue → deep navy gradient
- Tooltip shows flight count per airport

### Data
- Imported 2019–2020 historical flights (11 flights across 4 trips)
- Added 3 new airlines to Flighty importer: Air Malta, Cyprus Airways, Middle East Airlines

## 0.27.2 (2026-02-18)

### Projects Page
- Updated `fit` entry: refreshed description, expanded feature list, corrected tech stack to Python 3.9+, status changed from completed to active
- Updated `cfb` entry: rewrote description to explain CFB containers, expanded features, corrected tech stack to Python 3.8+, status changed from completed to alpha
- Updated `Miette` entry: rewrote description to clarify .doc reading focus, expanded features, corrected tech stack to Python 3.8+, status changed from completed to alpha
- Updated `TextAtAnyCost` entry: rewrote description with proper backstory, expanded features to list supported formats explicitly, corrected tech stack to PHP 8.3+

## 0.27.1 (2026-02-18)

### Calendar Improvements
- Country flag emojis on calendar days with flights (shows arrival countries)
- Plane icon for CZ-only return flight days
- Fixed plane icon invisible on half-day arrival cells (moved to bottom-left corner)

### Flights Map
- Country fill intensity scales with airport count (light peach → warm orange)
- Map shows only past flights (excludes future)
- Simplified legend to gradient only

### Travels Page
- Map view mode (visits/driving/drone/flights) persists in URL via `?view=` parameter

## 0.27.0 (2026-02-17)

### Flight Tracking
- Transport tab on trip edit page: add flights by number + date with AeroDataBox API auto-fill
- Flight lookup shows multiple legs (connecting flights) with airport names for selection
- Manual flight entry for when API is unavailable (historical or far-future flights)
- Auto-syncing flights_count: trip counter updates automatically when flights are added/deleted
- Self-healing: viewing the transport tab corrects any stale flight count
- Arrival date support for overnight flights with +1 badge
- Trip context bar on transport tab: dates, destinations, cities with flags for email cross-referencing
- API date range notice: warns when trip dates are outside AeroDataBox coverage (1 year back, ~6 weeks ahead)

### Flights on World Map
- New "Flights" layer on the Travels map with great-circle arc routes between airports
- Airport markers with names on hover
- Route thickness and opacity scale by flight count
- Countries with airports highlighted in warm background
- Legend shows route and airport counts

### Calendar Flight Icons
- Small plane icon on calendar days that have flights recorded
- New lightweight endpoint for fetching flight dates by year

### Mobile Improvements
- "Add Trip" and "Add Event" buttons collapse to icon-only on mobile
- ICS feed button hidden on mobile

### Database
- Migration 037: airports table (IATA code, name, city, country, coordinates, timezone) + flights table
- Migration 038: arrival_date column on flights for overnight flights

## 0.26.0 (2026-02-17)

### Photos Page Redesign
- Albums tab: year filtering with URL-driven pills — see one year at a time instead of all albums
- Map tab: world map with country photo fills — each country with photos shows its thumbnail cropped to the country shape
- Country album view: clicking a country opens all its photos grouped by trip
- Tripless photos supported (e.g. photos not linked to any trip appear in "Other photos" group)
- Microstate markers on the photo map (same pattern as Travels map)
- All views have shareable URLs: `/photos/albums/2025`, `/photos/map`, `/photos/map/163-spain`
- Back button from trip album navigates to the correct year

### Routes
- `/photos` redirects to `/photos/albums`
- `/photos/albums/:year` for year-filtered album view
- `/photos/map` for photo world map
- `/photos/map/:countrySlug` for country photo album

## 0.25.0 (2026-02-17)

### ICS Calendar Feed
- Shareable calendar feed URL for Google Calendar, Apple Calendar, or any iCal app
- All trips and personal events published as VEVENT entries
- Trips show destination names as summary, cities and description in details
- Personal events include category emoji in summary (e.g. "🏥 Doctor appointment")
- Token-protected URL — no login required for calendar apps
- Admin can generate, copy, and regenerate feed URL from the trips page
- Regenerating invalidates old links immediately

### Database
- Migration 036: New `app_settings` key-value table for application settings

### Dependencies
- Added `icalendar` library for RFC 5545 calendar generation

## 0.24.0 (2026-02-17)

### Vacation Balance Tracker
- Configurable departure/arrival types per trip: morning, half-day, or late evening
- Vacation day calculator: accounts for weekends, CZ public holidays, and partial days
- Vacation balance displayed on calendar page: spent + planned / remaining
- Half-cell gradient visualization on calendar for partial vacation days
- Faded cells for departure/arrival with zero vacation cost
- Only "regular" trips consume vacation days; work and relocation trips excluded

### Database
- Migration 033: Added departure_type and arrival_type columns to trips

### Fixes
- Fixed duplicate key error when updating trips (participants clear+reinsert race condition)
- Improved error message styling in trip form

## 0.23.0 (2026-02-16)

### Trip Info Tab — Extended Data
- Added languages, tipping guide, speed limits, visa-free days (CZ passport), EU roaming status, sunrise/sunset times
- Related data grouped together: adapter compatibility shown with sockets, speed limits with driving side, EU roaming with phone code, tipping with currency
- Smart currency display: weak currencies auto-multiplied (e.g. "1000 VND = 1.02 CZK"), full currency name shown
- Weather now shows min/max temperature range and rainy days count with icons
- Local time displayed instead of timezone offset
- Sunrise/sunset times for mid-trip date with day length
- Socket types use common names (EU, UK, Schuko, etc.) instead of type letters
- Info tab is now the default landing tab with its own URL (/info), refreshable
- Visa status color-coded (green for visa-free, red for visa required)

### Database
- Migration 032: Added languages, tipping, speed limits, visa-free days, EU roaming to UN countries
- Seeded extended reference data for all 193 UN member states

## 0.22.0 (2026-02-16)

### Trip Info Tab
- New "Info" tab on trip edit page with aggregated country reference data
- Per-country cards showing: power sockets (with visual icons), voltage, phone code, driving side, emergency number, tap water safety, currency exchange rates, weather averages, timezone offset from CET, and public holidays during trip
- Socket type illustrations (A through O) for quick visual identification
- Currency rates fetched live from ECB (31 currencies) with broader fallback (150+ currencies)
- Weather averages from Open-Meteo climate API using capital city coordinates
- Public holidays per country within trip dates (from Nager.Date API)
- TCC destinations grouped under their parent UN country

### Database
- Added 10 reference columns to UN countries table (sockets, voltage, phone code, driving side, emergency number, tap water, currency, capital coordinates, timezone)
- Seeded reference data for all 193 UN member states

## 0.21.1 (2026-02-16)

### Security
- Restricted CORS to explicit HTTP methods and headers (was `*`)
- Added max_length validation to contact form fields (name, subject, message)
- Removed Markdown parse_mode from Telegram notifications (prevents injection)
- Added `secure` flag to OAuth redirect cookie in production

### Code Quality
- Replaced deprecated `datetime.utcnow()` with `datetime.now(UTC)` (4 locations)
- Replaced stray `print()` with structured logging in Instagram gap-fill
- Replaced deprecated Pydantic `class Config` with `model_config = ConfigDict(...)`

### Testing
- Added test infrastructure with SQLite in-memory database
- Added 25 tests covering health, contact form, auth, admin users, and photos
- Added pytest step to CI pipeline

## 0.21.0 (2026-02-16)

### Performance
- Added composite database index for Instagram labeler navigation queries
- Photos index page loads thumbnails in batch (2-3 queries instead of N per trip)
- Travel stats page loads TCC destinations with eager-loaded country data
- Admin user list counts trips via SQL instead of loading all participations
- Location nearby search uses SQL bounding box pre-filter before distance calculation
- Trip create/update validates destinations and participants in batch queries
- Frontend code splitting: pages lazy-loaded on navigation (smaller initial bundle)
- Hero background image converted from JPG (305KB) to WebP (93KB)
- Removed unused `flag-icons` dependency (flags served from local SVGs)

## 0.20.1 (2026-02-16)

### Security Headers
- Fixed Content-Security-Policy to allow all external resources the site actually uses
- Added Cloudflare Turnstile domains to `script-src` and `frame-src`
- Added Google Fonts to `style-src` and `font-src`
- Added map tiles, Leaflet icons, and Google avatars to `img-src`
- Mozilla Observatory score: D → A/A+ (expected after deploy)

### Trip Form: Modal to Full Page
- Trip create/edit form is now a proper page instead of a modal overlay
- New URLs: `/admin/trips/new` and `/admin/trips/:id/edit` (bookmarkable, refreshable)
- Calendar date click navigates to `/admin/trips/new?date=YYYY-MM-DD`
- Back arrow replaces the X close button
- Fixes mobile usability: form scrolls naturally, all buttons always accessible (Save, Cancel, Delete were previously hidden behind iOS Safari bottom bar on 95vh modal)

## 0.20.0 (2026-02-16)

### Cover Photo Selection for Carousels
- Cover photo now remembers the specific image from a carousel post
- Previously, setting a carousel post as cover always showed the first image
- Star indicator on photos page now marks only the selected cover image, not the entire carousel
- When editing a cover post in the labeler, the carousel auto-scrolls to the selected cover image

### Location & Geocoding Improvements
- Reverse geocode now finds smaller settlements (hamlets, suburbs, counties)
- Local city search radius expanded from 15km to 50km for remote areas
- Zoom level increased from city (10) to village (14) for finer granularity
- Administrative prefixes stripped from city names (e.g., "Commune de Grand-Bassam" → "Grand-Bassam")

### Trip Editing Fixes
- City search in trip edit now filters by all trip countries (was only filtering for single-country trips)
- City-to-database links preserved when editing trip cities (were previously lost on save)

### Mobile UX Improvements
- Map legend and view toggle moved below map on mobile (were covering the map)
- Compact single-line legend with icon for "Show cities" toggle on mobile
- Trip edit dialog buttons: single row with icon-only delete button (fixes Safari bottom bar overlap)
- Photo lightbox captions now scrollable with thin translucent scrollbar

### Admin Improvements
- Partial cities shown individually in parentheses in trip table, preserving order
- "Close Ones" tab moved after Instagram tab
- Cover checkbox (C key) in labeler now captures the currently viewed carousel image

## 0.19.2 (2026-02-08)

### Bug Fixes
- Fixed visit dates being cleared when editing trips
- Location check-in data is now preserved when recalculating trip visits
- Modal max-height now accounts for iOS Safari safe area

## 0.19.1 (2026-01-31)

### Mobile Safari Fixes
- Fixed bottom buttons being overlapped by iOS Safari controls
- Added `viewport-fit=cover` and `safe-area-inset-bottom` padding to:
  - Location check-in FAB button
  - Location widget (non-admin view)
  - Modal action buttons
  - Trip form on admin page

### Photos Page
- Caption toggle button in lightbox to hide/show photo descriptions
- Eye icon appears next to Instagram link when photo has a caption
- Preference saved to localStorage (works for all visitors)

## 0.19.0 (2026-01-30)

### Photos Page UX Improvements
- Mobile-responsive Instagram labeler with compact layout for phone use
- Captions now display line breaks properly (CSS + database fix for escaped newlines)
- Hashtags stripped from captions on photos page
- Flag emoji on first line merged with description text
- URL slugs for trip pages (e.g., `/photos/218-spain-2026`)
- Cross-trip navigation in lightbox with peek/transition screen
- Keyboard arrow keys and on-screen buttons to browse between trips
- Instagram permalink icon in lightbox (next to close button)
- Photo counter moved to top-left corner
- "Show hidden trips" toggle as superscript eye icon (persisted to localStorage)
- "LIVE" badge on trips currently in progress (today between start/end dates)

### Admin Labeler Mobile Fixes
- Stats bar and sync buttons fit mobile width
- Trip selection buttons wrap to fit screen
- Action buttons (aerial, cover, skip, save) compact single-row layout
- Keyboard shortcuts hidden on mobile (tap-only interface)
- Moved "Unprocessed" and "Skipped" buttons to stats row with icons

### Bug Fixes
- Fixed trip hide button escaping to viewport (missing position:relative on parent)
- Fixed cross-trip navigation going to wrong photo index
- Fixed peek screen persisting after trip navigation

## 0.18.0 (2026-01-30)

### Photos Production Deployment
- Photos now served from Google Cloud Storage with public CDN URLs
- Storage abstraction supporting local (dev) and GCS (prod) backends
- Backend redirects to GCS URLs for optimal performance

### Photos Page Improvements
- Portrait aspect ratio (4:5) for trip thumbnails on index page
- "Classification in progress" subtitle while photo labeling continues
- Hide trips from photos page (admin only) - click eye icon on trip card
- Hidden trips fade out and auto-remove from list
- "Show hidden trips" checkbox to view/unhide hidden trips

### Database
- New `hidden_from_photos` field on trips for visibility control

## 0.17.0 (2026-01-30)

### Public Photos Page
- New `/photos` page displaying labeled Instagram photos grouped by year and trip
- Index view shows trips with photo counts and thumbnails, organized by year
- Trip detail view with responsive photo grid and lightbox viewer
- Keyboard navigation in lightbox: arrow keys to browse, Escape to close
- Lazy loading for optimal performance with large photo collections
- Photos nav item added to main navigation (after Projects)

### Cover Photo Selection
- Admins can set cover photo for each trip (shown as thumbnail on index)
- Star icon on trip photos page to select cover (admin only)
- Cover checkbox in Instagram labeler form (keyboard shortcut: C)
- Only one cover per trip (selecting new cover clears previous)
- Falls back to most recent photo if no cover is set

### Instagram Sync Improvements
- New "Fill gaps" feature to scan and recover missing posts
- Real-time progress indicator showing pages scanned and posts found
- Runs in background - continue labeling while scan progresses
- Fixed timezone comparison error when scanning for gaps
- Silently handles duplicate posts (no more log spam for IntegrityError)

### Bug Fixes
- Fixed React Hook warnings in Admin.tsx (missing dependencies)
- Wrapped callbacks in useCallback with proper dependency arrays

## 0.16.0 (2026-01-29)

### Instagram Post Labeler (Admin)
- New admin tool to categorize ~5k Instagram posts with travel metadata
- Keyboard-driven workflow: number keys (1-9) for trip selection, QWERTY row (q,w,e,r,t,y,u,i,o,p) for TCC destination, D for drone toggle, Enter to save, S to skip
- Arrow keys for navigation: ↑/↓ between posts, ←/→ for carousel images
- F to jump to next unprocessed post, K to jump to first skipped post
- Trip auto-suggestion based on post date (within trip or up to 2 months after)
- Auto-select TCC when trip has only one destination
- TCC search with autocomplete when no trip selected (press 0 for manual TCC entry)
- On-demand Instagram API fetching: "Fetch older" continues from last position, "Sync new" catches up with recent posts
- Pagination cursor management for efficient API usage
- Auto-fetch more posts when queue runs low (< 5 remaining)
- Post preloading: next 4 posts preloaded with images for instant navigation
- Rate limit detection with friendly "Take a break" screen
- Skeleton loading state with spinner (page structure stays visible)
- Stats bar showing labeled/skipped/remaining counts with fetching indicator
- Scrollable caption area for long post descriptions
- Edit previously labeled posts via URL navigation

### Backend
- Instagram Graph API integration with retry logic and exponential backoff
- Endpoints for post navigation, labeling, stats, and on-demand fetching
- Smart trip filtering: shows trips active during post date or ended within 2 months
- Cursor-based pagination with calibration for initial sync
- Fixed database session error when fetching duplicate posts (proper rollback on IntegrityError)
- Trip selector shows all destinations for multi-region trips (was limited to 3)

## 0.15.0 (2026-01-29)

### Real-Time Travel Updates ("Bragging" Feature)
- New countries appear immediately on check-in during trips (no need to wait for trip end)
- Counters (UN/TCC visited) update instantly when checking into a new country
- Map colors update in real-time as you check in to new destinations
- Stats page shows checked-in countries for anonymous users, all planned destinations for logged-in users
- Ongoing trip days show actual days traveled (not full planned duration) for anonymous users

### Stats Page Fixes
- Fixed "first visit" flag for trips spanning multiple months (now tracks by trip, not month)
- Trip counts use trip start date (counted once trip begins)

## 0.14.5 (2026-01-28)

### Travel Statistics
- Visit dates now use trip end date instead of first day of month (more accurate)
- Location check-in records actual check-in date (most precise)
- Destinations only count as visited after trip ends (not when it starts)

## 0.14.4 (2026-01-28)

### Travel Map
- City markers showing visited cities as small dots on the map
- White dots for full visits, grey dots for partial visits
- Hover tooltip shows city name
- "Show cities" toggle in map legend (saved to browser)
- Birthplace and home locations shown as gold stars
- Fixed 88 cities with wrong coordinates or country codes
- Removed Luxembourg and Brunei from microstate markers (now visible on map)

## 0.14.3 (2026-01-28)

### Performance
- Added database indexes for faster travel page queries
- Improved database connection pool settings for Cloud SQL

### Development
- Removed SQLite from dev defaults (MySQL only)

## 0.14.2 (2026-01-28)

### Home Page
- Added "an amateur Cosplayer" to rotating intro text
- Fixed "Traveller" → "Traveler" (US English spelling)
- Changed "Python professional" → "Python Developer"

### CV Page
- Added Cosplay to interests
- Added AI tools (Claude, Augment, ChatGPT) to hard skills
- Changed English proficiency to "Fluent"
- Fixed capitalization (JavaScript, uWSGI, job titles)
- Improved grammar and phrasing throughout
- Modernized Hard Skills (removed dated items, added GitHub Actions/GitLab CI)
- Changed "Over 18 years" to "since 2005" (evergreen)
- Added PDF export via Puppeteer (`make cv-pdf`) with custom fonts and styling

## 0.14.1 (2026-01-28)

### Mobile Responsive Improvements
- Trip form modal now fits mobile screens without horizontal scrollbar
- Date picker shows single month on mobile with centered backdrop overlay
- Date picker left-aligned on desktop (no more clipping on narrower screens)
- Admin page content properly padded on mobile when sidebar hidden
- Contact page map no longer overlaps mobile menu

### Stats Carousel (Mobile)
- Stats widgets display as carousel on mobile (one at a time)
- Swipe left/right to navigate between widgets
- Auto-advances every 5 seconds
- Navigation dots show current position
- UN Countries widget shown first

### Map & Layout
- Map fills remaining screen space on mobile
- Sticky footer stays at bottom of viewport
- Stats widgets equal width on desktop
- Fixed menu left padding asymmetry

### Admin UI
- NM Regions upload: click card instead of separate button (desktop only)

## 0.14.0 (2026-01-27)

### Driving & Drone Tracking
- Track driving (rental or own car) and drone flights per UN country
- New stat card showing countries driven and droned
- Activity badges (car/drone icons) displayed on UN country list
- Admin modal to edit driving/drone status by clicking on visited countries

### Interactive Map Views
- New map view toggle: Visits / Driving / Drone
- Driving view: blue = rental car, red = own car
- Drone view: purple = flew drone
- Dynamic legend updates based on selected view

### UI Improvements
- Wider country list columns (3 columns instead of 4)
- Aligned activity badges and dates on country rows
- Microstate markers now have hover highlighting

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
