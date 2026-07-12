# Transport Hire Management System (THMS)

A Flask web app for managing hire-purchase (lease-to-own) vehicle operations for a Nigerian transport business — drivers, vehicles, contracts, payments, expenses, and reports.

## Tech Stack

- **Backend:** Python 3.12, Flask 3.x, SQLAlchemy 2.x
- **Database:** PostgreSQL in production; falls back to local SQLite (`thms.db`) when `DATABASE_URL` is not set
- **Frontend:** Jinja2 templates, Bootstrap 5, vanilla JavaScript
- **Auth:** Flask-Login with bcrypt password hashing

## Running the App

The "Start application" workflow runs `python run.py`, serving on port 5000. Dependencies are managed via `requirements.txt` (installed through Replit's Python package manager).

Default login accounts (change immediately in a real deployment):
- `owner` / `owner123`
- `developer` / `dev123`

## Project Structure

See `backend/` (app factory, models, routes, templates, static assets) and `frontend/` (PWA manifest/service worker only — the actual UI is server-rendered via Jinja2). `run.py` is the entry point.

## User preferences

None recorded yet.
