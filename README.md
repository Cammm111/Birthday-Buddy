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

### Setup Instructions
## 1. Clone the repository

```bash
git clone https://github.com/Cammm111/birthday-buddy.git
cd birthday-buddy
```

## 2. Copy/Configure environment 
```bash
cp config/.env.template config/.env # Edit config/.env with your values
```

## 3. Build & Start w/ Docker Compose
```bash
docker compose -f config/docker-compose.yaml up --build
```

## 4. Access Birthday Buddy!
 - Swagger UI: `http://localhost:8000/docs`
 - OpenAPI JSON: `http://localhost:8000/openapi.json`

## Stopping/Starting Stack
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

### Architecture Explanation
## Project Structure
| Path          | Description                                                                          |
| ------------- | ------------------------------------------------------------------------------------ |
| `app/`        | Main application package. Bootstraps logging, database, scheduler, and routers.      |
| `app/main.py` | Starts the FastAPI app, sets up logging, mounts routers, and launches the scheduler. |

## Core Infrastructure
| Path                         | Description                                                                                 |
| ---------------------------- | ------------------------------------------------------------------------------------------- |
| `app/core/config.py`         | Loads environment variables with Pydantic, sets up bcrypt hasher, and exposes app settings. |
| `app/core/db.py`             | Initializes SQLModel engine, Redis client, creates tables, and seeds the admin user.        |
| `app/core/logging_config.py` | Sets up timestamped log files and root logger configuration using `dictConfig`.             |

## Models
| Path                            | Description                                                                             |
| ------------------------------- | --------------------------------------------------------------------------------------- |
| `app/models/user_model.py`      | SQLModel definition for User, with relationships to Birthday and Workspace.             |
| `app/models/birthday_model.py`  | SQLModel definition for Birthday, with one-to-one to User and many-to-one to Workspace. |
| `app/models/workspace_model.py` | SQLModel definition for Workspace, linking to many Users and Birthdays.                 |

## API Routes
| Path                            | Description                                                                      |
| ------------------------------- | -------------------------------------------------------------------------------- |
| `app/routes/user_route.py`      | Endpoints for listing, updating, and managing users.                |
| `app/routes/birthday_route.py`  | Endpoints for managing birthdays. Users get scoped access, admins get full CRUD. |
| `app/routes/workspace_route.py` | Endpoints for listing and managing workspaces (admin-only for mutations).        |
| `app/routes/utils_route.py`     | Admin utilities for cache, sync, and background job triggers.                    |

## Schemas
| Path                              | Description                                                      |
| --------------------------------- | ---------------------------------------------------------------- |
| `app/schemas/user_schema.py`      | Pydantic models for creating, reading, and updating users.       |
| `app/schemas/birthday_schema.py`  | Pydantic models for CRUD operations on birthdays.                |
| `app/schemas/workspace_schema.py` | Pydantic models for managing workspace data.                     |
| `app/schemas/utils_schema.py`     | Models used by utility routes (e.g. timezones, cache results).   |

## Services
| Path                                  | Description                                                                   |
| ------------------------------------- | ----------------------------------------------------------------------------- |
| `app/services/auth_service.py`        | Integrates FastAPI Users with SQLModel, handles JWT auth and user management. |
| `app/services/user_service.py`        | Business logic for managing users, including syncing with birthdays.          |
| `app/services/birthday_service.py`    | Handles birthday CRUD, integrity checks, and Redis cache invalidation.        |
| `app/services/workspace_service.py`   | Admin logic for managing workspaces and linked entities.                      |
| `app/services/scheduler_service.py`   | Sets up daily job to notify Slack of birthdays.                               |
| `app/services/slack_service.py`       | Sends messages to Slack with retry and logging support.                       |
| `app/services/redis_cache_service.py` | Manages Redis caching for birthday lookups with namespace handling.           |

## Tests
| Path                         | Description                                 |
| ---------------------------- | ------------------------------------------- |
| `app/tests/user_test.py`     | Tests user CRUD operations and validations. |
| `app/tests/birthday_test.py` | Tests birthday-related functionality.       |



### Supporting Systems
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