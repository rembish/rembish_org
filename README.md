# rembish.org

Personal website / portfolio.

## Stack

- **Frontend:** React 18 + TypeScript + Vite
- **Backend:** FastAPI + SQLAlchemy
- **Database:** MySQL 8 (dev), Cloud SQL MySQL (prod)
- **Auth:** Google OAuth (single admin user)

## Development

Prerequisites: Docker and Docker Compose

```bash
# Start dev environment
docker compose -f docker-compose.dev.yaml up --build

# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
```

### Environment Variables

Copy the example and fill in your values:

```bash
cp app/backend/.env.example app/backend/.env.dev
```

Required for full functionality:
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - OAuth login
- `TELEGRAM_TOKEN` / `TELEGRAM_CHAT_ID` - Contact form notifications

## Project Structure

```
app/
├── frontend/          # React + Vite
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── hooks/
│   └── public/
└── backend/           # FastAPI
    ├── src/
    │   ├── auth/
    │   └── models/
    └── alembic/       # Migrations
```

## Pages

- **Home** - Landing page
- **CV** - Curriculum Vitae
- **Contact** - Contact form with spam protection

## License

See [LICENSE](LICENSE) file.
