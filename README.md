# Transport Hire Management System (THMS)

A production-quality web application for managing hire-purchase (lease-to-own) vehicle operations for a Nigerian transport business.

## Tech Stack

- **Backend:** Python 3.11, Flask 3.x, SQLAlchemy 2.x
- **Database:** PostgreSQL (SQLite compatible)
- **Frontend:** Jinja2 templates, Bootstrap 5, Vanilla JavaScript
- **Auth:** Flask-Login with bcrypt password hashing

## Default Login Credentials

| User       | Password   | Role      |
|------------|------------|-----------|
| owner      | owner123   | Owner     |
| developer  | dev123     | Developer |

> **Change these passwords immediately after first login.**

## Project Structure

```
backend/
  __init__.py          # Flask app factory
  config.py            # Configuration classes
  extensions.py        # db, login_manager
  models/              # SQLAlchemy models
    user.py            # Users & auth
    driver.py          # Driver records
    vehicle.py         # Vehicle fleet
    contract.py        # Hire-purchase contracts
    payment.py         # Payment records
    expense.py         # Driver loans/expenses
    audit.py           # Permanent audit log
  routes/              # Flask blueprints
    auth.py            # Login/logout
    dashboard.py       # Main dashboard
    drivers.py         # Driver management
    vehicles.py        # Vehicle management
    payments.py        # Payment recording
    reports.py         # Report generation
    archives.py        # Archived records
    developer.py       # Developer tools
    settings.py        # Account settings
  templates/           # Jinja2 HTML templates
  static/
    css/custom.css     # Custom stylesheet
    js/app.js          # Main JavaScript
run.py                 # Application entry point
requirements.txt       # Python dependencies
```

## Running the App

```bash
pip install -r requirements.txt
python run.py
```

### Production deployment

For production installs, THMS requires a shared PostgreSQL database. Set one of the following before launching THMS:

- `DATABASE_URL` (preferred), for example:
  `postgresql+psycopg2://user:password@db-host:5432/thms`
- or the equivalent parts:
  `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

On Windows, you can set these as system environment variables so every installed THMS instance uses the same live database.

On Windows, THMS uses a system tray icon for a desktop-style experience. If you install the dependencies from `requirements.txt`, the tray menu will provide:

- `Open THMS`
- `Restart THMS`
- `Exit THMS`

The app runs on `http://0.0.0.0:5000`.

## Modules Built

- [x] Authentication (login/logout, password change)
- [x] Dashboard (stats, recent payments, quick actions)
- [x] Driver Management (add, list, view, search, paginate)
- [x] Vehicle Management (add, list, view, search, paginate)
- [x] Payment Recording (record, list, filter)
- [x] Reports (UI scaffolded — export coming)
- [x] Archives (searchable permanent records)
- [x] Settings (password change)
- [x] Developer Mode (audit log, system info)
- [x] Dark mode toggle
- [x] Collapsible sidebar
- [x] Mobile responsive

## Coming Next

- [x] Hire-purchase contract creation workflow
- [x] PDF/Excel/CSV report exports
- [x] Loan management (extra expenditure)
- [x] Capital management module
- [ ] Driver photo & document uploads
- [x] Automatic weekly payment calculations
- [x] Missed week detection & alerts
- [x] Backup & restore
