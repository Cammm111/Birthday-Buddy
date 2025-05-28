# Birthday Buddy

**Birthday Buddy** is a multi-tenant SaaS application that manages user's birthdays and sends personalized Slack notifications to each workspace (Slack channel). Built for collaboration and scalability, it includes user authentication, Redis caching, structured logging, and Slack integration.

## Tech Stack

|    Component     |        Technology       |
|------------------|-------------------------|
| Backend          | Python 3.12 + FastAPI   |
| Database         | PostgreSQL              |
| ORM              | SQLModel                |
| Caching          | Redis                   |
| Auth             | FastAPI Users (JWT)     |
| Scheduler        | APScheduler             |
| Notifications    | Slack Webhook API       |
| Logging          | Python logging + File   |
| Containerization | Docker & Docker Compose |

## Features

- JWT-based user authentication
- Multi-workspace support
- CRUD operations for Users, Birthdays, and Workspaces
- Redis-backed caching of birthday listings
- Daily Slack notifications for birthdays
- Admin utilities for cache inspection and data sync
- Timestamped log files in `/logs/` per run


## Authentication

Authentication is powered by FastAPI Users. User passwords are securely hashed using **bcrypt**. All protected routes require a valid JWT.

Auth Endpoints:
- `POST /auth/jwt/login`        – obtain a JWT
- `POST /auth/jwt/logout`       – invalidate the current JWT
- `POST /auth/register`         – create a new user (password hashed with bcrypt)
- `POST /auth/forgot-password`  – request a password reset 
- `POST /auth/reset-password`   – perform a password reset

## Setup Instructions
### 1. Clone the repository

```bash
git clone https://github.com/Cammm111/birthday-buddy.git
cd birthday-buddy
```

### 2. Copy/Configure environment 
```bash
cp config/.env.template config/.env # Edit config/.env with your values
```

### 3. Build & Start w/ Docker Compose
```bash
docker compose -f config/docker-compose.yaml up --build
```

### 4. Access Birthday Buddy!
 - Swagger UI: `http://localhost:8000/docs`
 - OpenAPI JSON: `http://localhost:8000/openapi.json`

### Stopping/Starting Stack
```bash
docker stop $(docker ps -aq --filter label=com.docker.compose.project=birthday-buddy)
```

```bash
docker start $(docker ps -aq --filter "label=com.docker.compose.project=birthday-buddy")
```

## Environment Variables

|      Variable      |               Description              |
|--------------------|----------------------------------------|
| `JWT_SECRET`       | JWT secret for authentication <string> |
| `SLACK_WEBHOOK_URL`| Default Slack Webhook <string>         |
| `ADMIN_EMAIL`      | Admin default email <string>           |
| `ADMIN_PASSWORD`   | Admin default password <string>        |
| `ADMIN_DOB`        | Admin default Date of Birth <string>   |
| `REDIS_URL`        | Redis connection <string>              |
| `DATABASE_URL`     | PostgreSQL connection <string>         |

## Sample endpoints:
- `GET /birthdays/` — List birthdays in current user’s workspace (authenticated user only)
- `POST /workspaces/` — Create a workspace (admin only)
- `PATCH /users/{user_id}` — Update user and sync birthday (admin only)

## Admin Utilities

| Endpoint                                  | Description                     |
|-------------------------------------------|---------------------------------|
| `POST /utils/run-birthday-job`            | Trigger Slack birthday job      |
| `GET /utils/cache/birthdays/{user_id}`    | Inspect Redis cache             |
| `DELETE /utils/cache/birthdays/{user_id}` | Invalidate cache                |
| `POST /utils/refresh-birthday-table`      | Sync birthdays from users       |
| `POST /utils/backfill-birthdays`          | Create missing birthdays        |

## Architecture Explanation
app/                        # This is the main application package. It contains the following submodules:

 - main.py                  # Sets up logging, loads environment variables, initializes database (and 
                              seeds the admin user), initializes Birthday Buddy app, starts the scheduler service, and mounts routers
---------------------------------------------------------------------------------------------------------------------------------
app/core/                   # Infrastructure code
  - config.py               # Defines a Pydantic Settings class that reads environment variables from 
                              config/.env, sets up a BCrypt password‐hasher, provides a hashed_admin_password property for seeding the admin user, and instantiates that global Settings class

  - db.py                   # Creates SQLModel engine, aliases SessionLocal for session 
                              creation, defines Redis client, defines init_db() to create all tables, look up existing superuser, insert the admin user if missing (catching and rolling back any IntegrityError to handle startup race conditions), and provides get_session() as a FastAPI dependency to yield and clean up database sessions

  - logging_config.py       # Creates a logs/ directory (if missing), generates a timestamped logfile 
                              name, and applies a dictConfig that attaches console and file handlers to the root logger and Uvicorn loggers at INFO level.
---------------------------------------------------------------------------------------------------------------------------------
app/models/                 # Defines database models using SQLModel including relationships and 
                              foreign keys

  - birthday_model.py       # Defines the Birthday SQLModel table (birthday). Enforces a uniqueness constraint on user_id and 
                              sets up bidirectional relationships: a one-to-one link to User and a one-to-many link to Workspace.

  - user_model.py           # Defines the User SQLModel table (user). It establishes a one-to-one relationship with Birthday (so 
                              each user has at most one birthday record) and a many-to-one relationship with Workspace (so many users can share a workspace). It exposes an id property aliasing user_id for compatibility with FastAPI-Users.
                              
  - workspace_model.py      # Defines the Workspace SQLModel table (workspace). It sets up one-to-many relationships to User (so 
                              a workspace can contain many users) and to Birthday (so a workspace can host many birthday entries).
---------------------------------------------------------------------------------------------------------------------------------
app/routes/                 # FastAPI routes that are organized by domain/feature 

  - /birthday_route         # Defines /birthday router with endpoints for birthday records. Authenticated users can 
                              list, update, and delete only their own entries, while admins gain additional routes to list all birthdays and create new ones. All data access/mutations are delegated to the birthday_service, and each endpoint is annotated with OpenAPI metadata.

  - /users_route            # Defines the /users router with endpoints for user management. Authenticated users can list members 
                              of their own workspace and update only their own profile. Admins can list all users and delete any account. All data access/mutations delegate to the user_service and each endpoint is annotated with OpenAPI metadata.

  - /utils_route            # Because sometimes Admins just want an EASY button

  - /workspace_route        # Manages workspaces (these group users and controls Slack webhook targets)
---------------------------------------------------------------------------------------------------------------------------------
app/schemas/                # Where those API dreams meet data validation reality...Pydantic-compatible 
                              schemas for request and response validation of payloads. Separate from
                              the SQLModel in models/ to control API surface w/o touching the database
  - birthday_schema.py      # Birthday schema
  - user_schema.py          # User schema
  - workspace_schema.py     # Workspace schema
---------------------------------------------------------------------------------------------------------------------------------
app/services/               # Where the actual business logic lives (not just a buzzword, I promise)
  - auth_service.py         # Handles FastAPI users config and JWT auth
  - birthday_service.py     # CRUD and syncing logic for birthday records
  - redis_cache_service.py  # Caching utility functions
  - scheduler_service.py    # Chronjob for posting Slack birthday messages
  - slack_service.py        # Birthday Buddy's entire personality
  - user_service.py         # Manages user updates
  - workspace_service.py    # Manages workspace updates
---------------------------------------------------------------------------------------------------------------------------------
app/tests/                      # Exists. Runs. Mostly passes... [**IN DEVELOPMENT**]
  - birthday_test.py        # Tests birthday CRUD operations
  - user_test.py            # Tests user CRUD operations


## Supporting Systems
- PostgreSQL (Docker)       # Stores all persistent data (users, birthdays, workspaces) in a PostgreSQL 
                              container
- Redis (Docker)            # Caches birthday lists by user to reduce database load
- Slack Webhooks            # Slack channels receive birthday messages based on the workspace 
                              configuration
- APScheduler               # Schedules and runs the birthday_job daily at 9am
- Logging                   # Timestamps and logs all service activity to /logs/, with a new .log file 
                              created per app restart

## License
Birthday Buddy Studios (aka my attic) © 2025 Cameron Manchester