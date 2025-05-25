# Birthday Buddy

**Birthday Buddy** is a multi-tenant SaaS application that manages user birthdays and sends personalized Slack notifications to each workspace (Slack channel). Built for collaboration and scalability, it includes user authentication, Redis caching, structured logging, and Slack integration — all powered by FastAPI.

## Tech Stack

| Component        | Technology             |
|------------------|------------------------|
| Backend          | Python 3.12 + FastAPI  |
| Database         | PostgreSQL             |
| ORM              | SQLModel               |
| Caching          | Redis                  |
| Auth             | FastAPI Users (JWT)    |
| Scheduler        | APScheduler            |
| Notifications    | Slack Webhook API      |
| Logging          | Python logging + File  |
| Containerization | Docker-ready           |

## Features

- JWT-based user authentication
- Workspace support with per-user and per-birthday ownership
- CRUD operations for Users, Birthdays, and Workspaces
- Redis-backed caching of birthday listings
- Scheduled Slack messages on user birthdays
- Admin-only utilities for cache inspection and birthday sync
- Per-run timestamped log files for observability

## Authentication

Authentication is powered by FastAPI Users. All protected routes require a valid JWT.

Endpoints:
- `POST /auth/jwt/login`
- `POST /auth/register`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/Cammm111/birthday-buddy.git
cd birthday-buddy
```

### 2. Create `.env`

```ini
DATABASE_URL=postgresql://buddy:password@localhost:5432/birthdaydb
REDIS_URL=redis://localhost
SECRET=your_jwt_secret
```

### 3. Create & activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 4. Start the app

```bash
uvicorn app.main:app --reload
```

## Environment Variables

| Variable       | Description                        |
|----------------|------------------------------------|
| `DATABASE_URL` | PostgreSQL connection string       |
| `REDIS_URL`    | Redis connection string            |
| `SECRET`       | JWT secret for authentication      |

## API Usage

Auto-generated API docs:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI: `http://localhost:8000/openapi.json`

Sample endpoints:
- `GET /birthdays/` — List birthdays in user’s workspace
- `POST /workspaces/` — Create a workspace
- `PATCH /users/{user_id}` — Update user and sync birthday

## Admin Utilities

| Endpoint                                  | Description                     |
|-------------------------------------------|---------------------------------|
| `POST /utils/run-birthday-job`            | Trigger Slack birthday job      |
| `GET /utils/cache/birthdays/{user_id}`    | Inspect Redis cache             |
| `DELETE /utils/cache/birthdays/{user_id}` | Invalidate cache                |
| `POST /utils/refresh-birthday-table`      | Sync birthdays from users       |
| `POST /utils/backfill-birthdays`          | Create missing birthdays        |

## Architecture Overview

                              ┌─────────────────────────────┐
                              │            Users            │
                              └──────────────┬──────────────┘
                                             │
                                             ▼
                              ┌──────────────────────────────┐
                              │      FastAPI Application     │
                              └──────────────┬───────────────┘
       ┌─────────────────────────────────────┼────────────────────────────────────┐
       │                                     │                                    │
       ▼                                     ▼                                    ▼
┌───────────────┐                  ┌──────────────────┐                ┌────────────────────┐
│  Auth_Service │◄─────JWT─────────│   API Routers    │                │  Scheduler Service │
│ (FastAPI Users│                  │ (/auth, /users,  │                │    (APScheduler)   │
│   + bcrypt)   │                  │  /birthdays, etc)│                │                    │
└───────────────┘                  └──────────────────┘                └──────────┬─────────┘
                                                                                  |
                                                                                  ▼
                                                                     ┌──────────────────────────┐
                                                                     │    Slack Webhook API     │
                                                                     │ (Per-workspace endpoint) │
                                                                     └──────────────────────────┘


      ┌────────────────────────────────────────────────────────────────────────────────────────────┐
      ▼                                                                                            ▼
┌───────────────┐          Read/Write          ┌───────────────┐         Cache Read         ┌─────────────┐
│ PostgreSQL DB │◄────────────────────────────►│ SQLModel ORM  │◄───────────────┐           │ Redis Cache │
│ (Users,       │                              │  (Sessions)   │                │           └─────────────┘
│ Birthdays,    │                              └───────────────┘                │
│ Workspaces)   │                                                               └───set/get/invalidate
└───────────────┘

## Architecture Explanation
app/                        # This is the main application package. It contains the following submodules:

- main.py                   # Initializes the FastAPI app, mounts routers, sets up logging, and starts the scheduler

core/                       # Shared infrastructure code
  - config.py               # Loads environment variables
  - db.py                   # Initializes the SQLModel database engine
  - logging_config.py       # Configures file & console logging

models/                     # Defines database models using SQLModel including relationships and foreign keys
  - birthday_model          # Birthday model w/ relationships & FKs
  - user_model              # User model w/ relationships & FKs
  - workspace_model         # Workspace model w/ relationships & FKs

schemas/                    # Where API dreams meet data validation reality... Pydantic-compatible schemas for request and 
                              response validation of payloads. Separate from the SQLModel ORM in models/ to control API surface without touching the database
  - birthday_schema         # Birthday schema
  - user_schema             # User schema
  - workspace_schema        # Workspace schema

routes/                     # FastAPI routers that are organized by domain where each route file delegates business logic to a 
                              corresponding service layer
  - /birthday_route         # Manage birthdays
  - /users_route            # Manage user accounts
  - /utils_route            # Because sometimes Admins just want a button
  - /workspace_route        # Manage workspaces, which groups users and controls Slack webhook targets

services/                   # Where the actual business logic lives (not just a buzzword, I promise)
  - auth_service.py         # Handles FastAPI Users config and JWT auth
  - birthday_service.py     # CRUD and syncing logic for birthday records
  - redis_cache_service.py  # Caching utility functions
  - scheduler_service.py    # Daily job for posting Slack birthday messages
  - slack_service.py        # Birthday Buddy's entire personality
  - user_service.py         # Manage user updates
  - workspace_service.py    # Manage workspace updates

tests/                      # Exists. Runs. Mostly passes...
  - birthday_test.py        # Tests birthday CRUD operations
  - user_test.py            # Tests user CRUD operations

## Supporting Systems
- PostgreSQL (Docker)       # Stores all persistent data (users, birthdays, workspaces) in a PostgreSQL container
- Redis (Docker)            # Caches birthday lists by user to reduce database load
- Slack Webhooks            # Slack channels receive birthday messages based on the workspace configuration
- APScheduler               # Schedules and runs the birthday_job daily at 9am
- Logging                   # Timestamps and logs all service activity to /logs/, with a new .log file created 
                              per app restart
## License
Birthday Buddy Studios © 2025 Cameron Manchester