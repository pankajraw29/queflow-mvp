# QueueFlow

A queue-management web app: businesses create queues, customers join via a QR code or link, see their live position, and get called when it's their turn.

**Stack:** FastAPI + MongoDB (backend), React + Vite (frontend).

## Features

- Business accounts with JWT auth (bcrypt-hashed passwords)
- Create / rename / open / close / delete queues
- Public join links + QR codes — customers join with just their name
- Atomic sequential ticket numbering (A01, A02, …)
- Live ticket status polling with an "It's your turn!" state
- Call Next / Complete / Skip / Reset controls for staff
- Rate-limited public endpoints

## Project layout

```
queueflow/
├── backend/        # FastAPI API (see backend/README below)
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── auth.py
│       ├── models.py
│       ├── db.py
│       ├── ratelimit.py
│       └── routers/  # auth.py, queues.py, public.py
└── frontend/       # React + Vite SPA
```

## Quick start (local)

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit MONGO_URL / JWT_SECRET
uvicorn app.main:app --reload --port 8000
```

Needs MongoDB — locally via `mongod`, or a free [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) cluster.

**Frontend**

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:5173.

## API overview

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /api/auth/register | – | Create business account |
| POST | /api/auth/login | – | Log in |
| GET | /api/auth/me | Bearer | Current business |
| POST | /api/queues | Bearer | Create queue |
| GET | /api/queues | Bearer | List my queues |
| GET | /api/queues/{id} | Bearer | Queue + active tickets |
| PATCH | /api/queues/{id} | Bearer | Rename / open / close |
| DELETE | /api/queues/{id} | Bearer | Delete queue |
| POST | /api/queues/{id}/call-next | Bearer | Serve next ticket |
| POST | /api/queues/{id}/complete-current | Bearer | Finish current ticket |
| POST | /api/queues/{id}/skip-current | Bearer | Skip current ticket |
| POST | /api/queues/{id}/reset | Bearer | Clear tickets, restart at A01 |
| GET | /api/pub/q/{code} | – | Public queue info |
| POST | /api/pub/q/{code}/join | – | Join queue (name only) |
| GET | /api/pub/q/{code}/t/{ticket} | – | Poll ticket status |

## Deploying for free

See [DEPLOY.md](DEPLOY.md) — MongoDB Atlas + Render + Vercel, ₹0.

## Tests

```bash
cd backend
.venv/bin/python -m pytest tests/ -q
```

Tests run against an in-memory fake MongoDB (`tests/fake_db.py`), so no database server is needed.
