# Transport Hire Management System (THMS)

A production-quality web application for managing hire-purchase (lease-to-own) vehicle operations for a Nigerian transport business.

## Tech Stack

- **Backend:** Python 3.11/3.12, Flask 3.x, SQLAlchemy 2.x
- **Database:** SQLite (dev) / PostgreSQL via `DATABASE_URL` env var (prod)
- **Frontend:** Jinja2 templates, Bootstrap 5, Vanilla JavaScript
- **Auth:** Flask-Login with bcrypt password hashing

## How to Run

```bash
python run.py
```

The app runs on `http://0.0.0.0:5000`. The workflow "Start application" handles this automatically.

## Default Login Credentials

| User      | Password  | Role      |
|-----------|-----------|-----------|
| owner     | owner123  | Owner     |
| developer | dev123    | Developer |

> **Change these passwords after first login.**

## Environment Variables

| Variable       | Purpose                          | Default                        |
|----------------|----------------------------------|--------------------------------|
| `SECRET_KEY`   | Flask session signing key        | hardcoded dev fallback         |
| `DATABASE_URL` | PostgreSQL connection string     | SQLite (`thms.db` in project root) |
| `FLASK_ENV`    | `development` or `production`    | `development`                  |

The `SESSION_SECRET` Replit secret is available but the app currently reads `SECRET_KEY`. Rename or alias as needed.

## Project Structure

```
backend/
  __init__.py       # Flask app factory, DB init, migrations, seed
  config.py         # Config classes (Dev/Prod)
  extensions.py     # db, login_manager
  models/           # SQLAlchemy models
  routes/           # Flask blueprints
  templates/        # Jinja2 HTML templates
  static/           # CSS, JS, uploads
run.py              # Entry point
requirements.txt    # Python dependencies
```

## Modules

- Authentication, Dashboard, Drivers, Vehicles, Contracts, Payments, Expenses, Archives, Audit Log, Capital Management, Reports, Settings, Developer tools

## User Preferences

<!-- Add any user preferences here -->
