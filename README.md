# TowerOps

**Real-time job cost management for telecom construction project managers.**

TowerOps gives telecom PMs a single dashboard showing exactly where every dollar is going, whether they're on schedule, and where the problems are — updated automatically from the time-tracking apps their crews already use.

---

## Tech Stack

- **Frontend:** React 18 + TypeScript + Tailwind CSS + Vite (PWA)
- **Backend:** Python + FastAPI + SQLAlchemy
- **Database:** PostgreSQL 16
- **Cache:** Redis 7
- **Auth:** JWT (python-jose + passlib/bcrypt)

## Quick Start

### Option A: Docker (recommended)

```bash
cp .env.example .env
docker-compose up --build
```

- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

### Option B: Native

**Prerequisites:** Python 3.12+, Node.js 20+, PostgreSQL 16+, Redis 7+

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
alembic upgrade head           # Run migrations
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
TowerOps/
├── docker-compose.yml         # Local dev environment
├── .env.example               # Environment variables template
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI entry point
│   │   ├── config.py          # Settings (pydantic-settings)
│   │   ├── database.py        # SQLAlchemy engine + session
│   │   ├── models/            # Database models (ORM)
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── routers/           # API route handlers
│   │   ├── services/          # Business logic
│   │   │   └── integrations/  # Time-tracking adapters
│   │   └── utils/             # Auth, helpers
│   └── alembic/               # Database migrations
├── frontend/
│   ├── src/
│   │   ├── api/               # API client
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Page-level components
│   │   └── types/             # TypeScript type definitions
│   └── public/
│       ├── manifest.json      # PWA manifest
│       └── sw.js              # Service worker
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Register org + admin user |
| POST | `/api/v1/auth/login` | Login, get JWT token |
| GET | `/api/v1/auth/me` | Get current user |
| GET | `/api/v1/dashboard/stats` | Dashboard statistics |
| GET | `/api/v1/dashboard/projects` | Active project summaries |
| GET | `/api/v1/projects/` | List all projects |
| POST | `/api/v1/projects/` | Create project |
| GET | `/api/v1/projects/{id}` | Get project detail |
| PATCH | `/api/v1/projects/{id}` | Update project |
| GET | `/api/v1/projects/{id}/budget` | Get budget lines |
| POST | `/api/v1/projects/{id}/budget` | Add budget line |

## Integration Adapters

The adapter pattern normalizes time data from any clock-in/out platform:

```
[Workyard API]   → Workyard Adapter   → Normalized Time Entry
[Busybusy API]   → Busybusy Adapter   → Normalized Time Entry
[ExakTime API]   → ExakTime Adapter   → Normalized Time Entry
[ClockShark API] → ClockShark Adapter → Normalized Time Entry
[CSV Upload]     → CSV Parser         → Normalized Time Entry
```

Each adapter implements `TimeTrackingAdapter` in `backend/app/services/integrations/`.

## Roadmap

- [x] Project scaffolding
- [ ] Database migrations (Alembic)
- [ ] Workyard integration adapter
- [ ] CSV time import
- [ ] Real-time cost calculation engine
- [ ] Schedule/milestone tracking
- [ ] Document management
- [ ] Return trip auto-detection
- [ ] Oversized crew flagging
- [ ] Export reports (PDF/Excel)
