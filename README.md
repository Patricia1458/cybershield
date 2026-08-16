# CyberShield

Cybersecurity Awareness Training Platform with Simulated Phishing for Small Businesses.

**Live demo:** https://cybershield-web-production.up.railway.app

## What it does

CyberShield lets a small business owner register their organisation, invite employees, assign interactive cybersecurity training modules (phishing, smishing, vishing, social engineering, password security, pop-up phishing, evil twin Wi-Fi), run simulated phishing exercises, and track results through a live analytics dashboard.

## Tech stack

- **Backend:** Python 3, Django
- **Frontend:** HTML5, CSS3, Bootstrap 5, vanilla JavaScript, Chart.js
- **Database:** SQLite (local development) / PostgreSQL (production, via `dj-database-url`)
- **Auth & security:** Django's built-in authentication + a custom email-or-username backend, `django-axes` for login rate limiting, field-level encryption (`cryptography`) for stored email addresses
- **PDF generation:** `reportlab` (certificates)
- **Deployment:** Railway, served via Gunicorn + WhiteNoise

## Project structure

Four Django apps:

| App | Responsibility |
|---|---|
| `accounts` | Registration, login, organisations, employee invitations, roles |
| `training` | Training modules, quizzes, progress tracking, certificates |
| `phishing` | Phishing campaigns, message templates, click/report tracking |
| `dashboard` | Aggregated reporting and analytics for both roles |

## Running the backend locally

```bash
# clone and enter the project
git clone https://github.com/Patricia1458/cybershield.git
cd cybershield

# create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# install dependencies
pip install -r requirements.txt

# apply migrations
python manage.py migrate

# create an admin account
python manage.py createsuperuser

# (optional) seed demo training modules and phishing campaigns
python manage.py seed_all_content

# run the dev server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`. By default this runs against a local SQLite database (`db.sqlite3`); no extra configuration is needed.

## Environment variables (production)

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django's cryptographic signing key |
| `DJANGO_DEBUG` | `False` in production |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hostnames |
| `DATABASE_URL` | PostgreSQL connection string (provided automatically by Railway's Postgres service) |

## How the reporting statistics work

The dashboards under `dashboard/` and the admin analytics page under `phishing/` do not use hardcoded numbers. They query the database live on every page load:

- Training completion, quiz scores, and per-module progress come from `training.models.UserProgress`.
- Phishing click rates, report rates, and risk levels come from `phishing.models.PhishingResult`, filtered to the requesting administrator's own organisation.
- Chart data (e.g. `dashboard/views.py`) is computed with Django ORM aggregation (`Count`, `Q`) and passed to Chart.js as JSON.

Example: the admin analytics endpoint is `GET /phishing/analytics/`, backed by `phishing.views.analytics_view`, which aggregates `PhishingResult` and `PhishingCampaign` records for the logged-in administrator's organisation and returns them to the template as context.

## Testing

```bash
python manage.py test
```

The project includes 47 automated tests covering authentication, role-based access control, training/quiz logic, phishing simulation tracking, and cross-organisation data isolation.

## Security testing

A baseline OWASP ZAP scan was run against the live deployment. Reports are available under `docs/`.

## Author

Patricia Naamala — USIU-Africa, APT 4900A
