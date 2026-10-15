# PulseNotify — Flight Price Alert API

PulseNotify is a Django REST Framework API for creating flight price alerts, checking mock flight prices, and recording notifications when prices meet a user's target threshold.

## Features

- User registration and JWT-based authentication.
- User-specific flight price alerts.
- Soft deactivation of alerts.
- Mock flight-price endpoint with configured price ranges.
- Role-based admin summary endpoint.
- Celery background tasks for price checking and notification processing.
- PostgreSQL database and Redis message broker.
- Automated tests for authentication, alert access, permissions, and notification tasks.

## Technology Stack

- Python
- Django
- Django REST Framework
- Simple JWT
- PostgreSQL
- Redis
- Celery
- Docker Compose

## Prerequisites

- Python and pip
- Docker Desktop with Docker Compose
- Git
- Postman (for API testing)

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/jeyaprakashcse36-hue/PulseNotify
cd PulseNotify
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root. Configure the PostgreSQL database name, username, and password to match your Django database settings and Docker Compose configuration.

Do not commit `.env` or expose credentials in source control.

### 5. Start PostgreSQL and Redis

```powershell
docker compose up -d db redis
```

Check the services:

```powershell
docker compose ps
```

### 6. Apply database migrations

```powershell
python manage.py migrate
```

### 7. Start the Django development server

```powershell
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/`.

## API Endpoints

| Method | Endpoint | Purpose | Authentication |
|---|---|---|---|
| POST | `/api/register/` | Register a user | Public |
| POST | `/api/login/` | Authenticate and obtain JWT tokens | Public |
| GET | `/api/alerts/` | List the authenticated user's alerts | Required |
| POST | `/api/alerts/` | Create a price alert | Required |
| DELETE | `/api/alerts/<id>/` | Deactivate an owned alert | Required |
| GET | `/api/flights/price/?route=MAA-DEL` | Retrieve a mock flight price | Public |
| GET | `/api/admin/summary/` | Retrieve alert and notification statistics | ADMIN role |

The Django administration site is available at `/admin/`.

### Authentication

Obtain an access token from the registration or login endpoint. For protected endpoints, send the token in the HTTP header:

```text
Authorization: Bearer <access_token>
```

Regular users should only be able to access their own alerts. The admin summary endpoint requires a user whose profile has the `ADMIN` role.

### Mock Flight Prices

The flight-price endpoint returns a randomly generated price within the configured range for a supported route. It is a mock API, not a live airline pricing integration.

## Background Tasks

Celery is configured to schedule the `pulse.tasks.check_prices` task every 60 seconds.

Run the Celery worker in a separate PowerShell terminal:

```powershell
celery -A PulseNotify worker --pool=solo --loglevel=info
```

Run Celery Beat in another terminal:

```powershell
celery -A PulseNotify beat --loglevel=info
```

Keep the Django server, Redis, Celery worker, and Celery Beat running while testing scheduled price checks.

The price-checking task requests the application's mock flight-price endpoint. When a price meets an alert's threshold, it queues notification processing. The notification task records the notification and marks the alert as triggered, while checking the alert status to prevent duplicate processing.

## Testing

Run the automated test suite:

```powershell
python manage.py test pulse
```

Check the Django configuration:

```powershell
python manage.py check
```

Check installed package compatibility:

```powershell
python -m pip check
```

The current development test suite has passed 14 tests. Rerun the tests after making changes and before submission.

## Docker Services

The current `docker-compose.yml` defines:

- PostgreSQL 16, exposed on host port `5433`.
- Redis 7, exposed on host port `6379`.

Django, the Celery worker, and Celery Beat are started separately using the commands above.

## Security Notes

- Keep `.env` out of version control.
- Never store plaintext passwords; use Django's password hashing.
- Do not allow users to assign themselves the `ADMIN` role through registration input.
- Enforce ownership checks when retrieving or deactivating alerts.
- Use appropriate production settings and secret management before deploying outside local development.

## Project Status

The application has passed the current Django system check, dependency check, and 14 automated tests. Complete the final API regression tests and verify scheduled Celery Beat execution before considering the project ready for submission.
