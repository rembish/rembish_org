# rembish.org

Personal website and travel management platform.

## Stack

- **Frontend:** React 18 + TypeScript + Vite
- **Backend:** FastAPI + SQLAlchemy + Alembic
- **Database:** MySQL 8
- **Auth:** Google OAuth (role-based: admin, viewer)
- **AI:** Claude Haiku for document extraction (flights, car rentals, bookings)
- **Storage:** Google Cloud Storage (photos, vault files)
- **Deploy:** Google Cloud Run

## Public Pages

- **Home** — Landing page with rotating intro
- **CV** — Curriculum vitae with PDF export
- **Contact** — Contact form (Cloudflare Turnstile anti-spam, Telegram notifications)
- **Projects** — GitHub repositories
- **Travels** — Interactive world map with UN/TCC/NomadMania statistics, city markers, flight routes, driving/drone overlays
- **Photos** — Instagram photo gallery with albums by year, world map with country photo fills

## Admin Features

- **Trip management** — Calendar view, trip CRUD, date picker, destination/city search, participant tracking, vacation balance
- **Trip info** — Per-country reference cards: power sockets, currency rates, weather, holidays, health requirements, driving side, visa status, emergency numbers
- **Transport** — Flights (AeroDataBox lookup, ticket PDF extraction), car rentals, train/bus/ferry bookings — all with AI-powered document extraction
- **Stays** — Accommodation bookings with AI extraction from confirmation PDFs
- **Vault** — AES-256-GCM encrypted storage: passports, IDs, loyalty programs, vaccinations, travel documents with private file storage
- **Fixers** — Travel contacts with country assignment and trip integration
- **People** — Close ones management, postcard addresses with Nominatim autocomplete
- **Instagram labeler** — Keyboard-driven tool to categorize posts with travel metadata
- **ICS calendar feed** — Shareable feed for Google Calendar / Apple Calendar
- **Viewer role** — Read-only trip sharing for family members

## Development

Prerequisites: Docker and Docker Compose.

```bash
# Start dev environment
docker compose -f docker-compose.dev.yaml up --build

# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
```

### Environment Variables

```bash
cp app/backend/.env.example app/backend/.env.dev
```

Required for full functionality:
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — OAuth login
- `TELEGRAM_TOKEN` / `TELEGRAM_CHAT_ID` — Contact form notifications
- `ANTHROPIC_API_KEY` — AI document extraction
- `VAULT_ENCRYPTION_KEY` — Vault encryption (AES-256-GCM)

### Code Quality

```bash
make check    # runs all checks below
make lint     # ruff check + ruff format + eslint + prettier
make typecheck  # mypy + tsc --noEmit
```

### Tests

```bash
cd app/backend && pytest tests/ -v
```

## Project Structure

```
app/
├── frontend/
│   ├── src/
│   │   ├── pages/           # Route-level components
│   │   ├── components/
│   │   │   ├── admin/       # Admin panel tabs and forms
│   │   │   └── trip/        # Trip page tabs and modals
│   │   ├── hooks/
│   │   └── lib/             # Shared utilities (API helper, auth context)
│   └── public/
└── backend/
    ├── src/
    │   ├── auth/            # Google OAuth, sessions
    │   ├── admin/           # Vault, instagram, users, fixers
    │   ├── travels/         # Trips, flights, stays, transport, stats, photos
    │   ├── models/          # SQLAlchemy models
    │   └── data/            # Static reference data (health requirements)
    ├── alembic/             # 57 database migrations
    └── tests/               # 30 test modules
```

## License

[GNU Affero General Public License v3.0](LICENSE)
