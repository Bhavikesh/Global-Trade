# GlobalTrade.ai

AI-assisted global import-export (EXIM) operating platform.

---

## Project Status

**Phase 1 — Foundation: COMPLETE (T1.1 – T1.7)**

| Task | Description | Status |
|---|---|---|
| T0.1–T0.6 | Repository, backend, frontend, database, migrations, Auth0 | ✅ Complete |
| T1.1 | Backend JWT verification (Auth0 RS256) | ✅ Complete |
| T1.2 | User identity provisioning (first-login upsert) | ✅ Complete |
| T1.3 | User profile read/update | ✅ Complete |
| T1.4 | Organization creation + ADMIN membership | ✅ Complete |
| T1.5 | Organization membership management | ✅ Complete |
| T1.6 | RBAC + organization isolation | ✅ Complete |
| T1.7 | Company Profile (on Organization) | ✅ Complete |
| T1.8+ | Business Documents / Product / Buyer / Supplier / RFQ | 🔲 Planned |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, shadcn/ui |
| Backend | Python, FastAPI, Pydantic v2, SQLAlchemy 2.0 (sync), Alembic |
| Database | PostgreSQL + pgvector |
| Auth | Auth0 (RS256 JWT) |
| Object Storage | Deferred |

---

## Project Structure

```
GlobalTrade/
├── docs/              # Authoritative project documentation
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── DATA_MODEL.md
│   ├── DESIGN.md
│   ├── RULES.md
│   ├── AI_SPEC.md
│   ├── TASKS.md
│   ├── MEMORY.md
│   └── DECISIONS.md
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/v1/    # Route handlers
│   │   ├── core/      # Auth, config, permissions
│   │   ├── db/        # SQLAlchemy session
│   │   ├── models/    # SQLAlchemy ORM models
│   │   └── schemas/   # Pydantic schemas
│   ├── alembic/       # Database migrations
│   ├── tests/         # pytest test suite
│   ├── requirements.txt
│   └── .env.example
└── frontend/          # Next.js application
    ├── src/
    │   ├── app/       # Next.js App Router pages
    │   ├── components/ # Shared UI components
    │   └── lib/       # API client, auth, utilities
    ├── package.json
    └── .env.example
```

---

## Local Development Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 14+ with pgvector extension
- Auth0 account (see `.env.example` files)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database URL and Auth0 credentials

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your Auth0 credentials

# Start development server
npm run dev
```

### Running Tests

```bash
# Backend
cd backend && source .venv/bin/activate && pytest -v

# Frontend
cd frontend && npm run lint && npm run build
```

---

## API Overview

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/health` | Health check | Public |
| GET | `/api/v1/users/me` | Get/create current user | JWT |
| PATCH | `/api/v1/users/me` | Update user profile | JWT |
| POST | `/api/v1/organizations/` | Create organization | JWT |
| GET | `/api/v1/organizations/` | List my organizations | JWT |
| GET | `/api/v1/organizations/{id}` | Get organization + company profile | JWT + Member |
| PATCH | `/api/v1/organizations/{id}` | Update company profile | JWT + ADMIN |
| GET | `/api/v1/organizations/{id}/members` | List members | JWT + Member |
| POST | `/api/v1/organizations/{id}/members` | Add member | JWT + ADMIN |
| PATCH | `/api/v1/organizations/{id}/members/{mid}` | Update member role | JWT + ADMIN |
| DELETE | `/api/v1/organizations/{id}/members/{mid}` | Remove member | JWT + ADMIN |

---

## Team Development Workflow

### Branch Naming

```
feature/product-management     # Developer 1
feature/buyer-supplier         # Developer 2
feature/rfq-quotation          # Developer 3
feature/core-integration       # Team Lead
```

### Contribution Rules

1. **Never commit directly to `main`**
2. All work goes on a feature branch
3. Open a Pull Request → Team Lead review → merge
4. All PRs must pass: `pytest -v` + `npm run lint` + `npm run build`
5. Never commit `.env`, `.env.local`, or any secrets
6. Every new API endpoint requires backend authorization (no frontend-only guards)
7. Every organization-scoped record must be filtered by `organization_id`

### Database Migrations

- All schema changes must use Alembic — never modify the DB manually
- Coordinate migration ordering with the Team Lead before creating migrations
- Current migration head: `0002_phase1_identity`

---

## Authorization Model

Authorization is enforced entirely by the **backend**. Frontend is NOT a security boundary.

| Role | Description |
|---|---|
| `ADMIN` | Full organization management |
| `MEMBER` | Read-mostly access |
| `EXPORTER` / `IMPORTER` | Trade-specific operations (future) |
| `BUYER` / `SUPPLIER` | Workflow-specific access (future) |
| `OPERATIONS` / `FINANCE` / `COMPLIANCE` / `LOGISTICS` | Functional roles (future) |

Core enforcement functions in `backend/app/core/auth/permissions.py`:

- `get_membership_or_403()` — any active member
- `require_admin()` — ADMIN only
- `require_organization_membership(..., allowed_roles={...})` — specific roles

---

## Documentation

Read the `/docs` directory before implementing any feature:

| File | Purpose |
|---|---|
| `PRD.md` | Product requirements |
| `ARCHITECTURE.md` | System architecture |
| `DATA_MODEL.md` | Database schema and field definitions |
| `DESIGN.md` | UI/UX design system |
| `RULES.md` | Engineering rules |
| `AI_SPEC.md` | AI feature specification |
| `TASKS.md` | Implementation task list and status |
| `MEMORY.md` | Persistent project context |
| `DECISIONS.md` | Architecture decision records |
