# Aadhaar Analytics Portal
**Unlocking Societal Trends in Aadhaar Enrolment and Updates**

> Project by Shreyas Manish Mudholkar · Shraddha Pardeshi · Abid Abdulla · Zail Syed

---

## Project Overview

A full-stack web-based analytics portal that analyses Aadhaar enrolment, demographic, and biometric datasets to extract meaningful societal trends, detect anomalies, and generate actionable improvement recommendations.

### Modules Implemented
| Module | Description |
|--------|-------------|
| **Admin Auth** | JWT-based secure login |
| **Live Statistics** | Real-time KPI cards, gender/age/status charts |
| **Past History** | Monthly trend, YoY growth, regional comparison |
| **Insights & Improvement** | Rule-based recommendations + biometric quality |
| **Anomaly Detection** | Surge/drop/duplicate/quality flagging |
| **Data Export** | CSV download of any visible table |

---

## Folder Structure

```
aadhaar-portal/
├── backend/
│   ├── main.py                  # FastAPI application entry point
│   ├── database.py              # SQLAlchemy connection pool
│   ├── models/
│   │   └── models.py            # ORM models (Region, Enrollment, etc.)
│   └── routes/
│       ├── auth.py              # POST /api/auth/login
│       ├── live_stats.py        # GET  /api/live/*
│       ├── history.py           # GET  /api/history/*
│       ├── insights.py          # GET  /api/insights/*
│       └── anomalies.py         # GET  /api/anomalies/*
├── frontend/
│   └── pages/
│       ├── login.html           # Admin login page
│       └── dashboard.html       # Main analytics dashboard
├── database/
│   └── schema.sql               # MySQL schema + seed data
├── requirements.txt
└── README.md
```

---

## Setup Guide

### Prerequisites
- Python 3.11+
- MySQL 8.0+
- A modern web browser (Chrome/Firefox/Edge)

---

### Step 1 — Database Setup

```bash
# Log into MySQL
mysql -u root -p

# Run the schema
SOURCE /path/to/aadhaar-portal/database/schema.sql;
```

This creates the `aadhaar_analytics` database, all tables, seed regions, and a default admin user.

Create the admin account with `python scripts/create_admin.py`.

---

### Step 2 — Backend Setup

```bash
# Navigate to project root
cd aadhaar-portal

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Configure database connection

Create a `.env` file in the project root:

```env
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=aadhaar_analytics
```

Or set environment variables directly in your shell.

#### Run the backend server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

Interactive API docs: `http://localhost:8000/docs`

---

### Step 3 — Frontend Setup

No build step required. Simply open the HTML files in a browser or serve them with a local HTTP server:

```bash
# Using Python's built-in server (from frontend/pages directory)
cd frontend/pages
python -m http.server 3000
```

Then visit: `http://localhost:3000/login.html`

---

### Step 4 — First Login

1. Open `http://localhost:3000/login.html`
2. Log in with the account created by `scripts/create_admin.py`
4. You will be redirected to the main dashboard

---

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Get JWT token |
| GET  | `/api/auth/me`    | Get current admin info |

### Live Statistics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/live/summary` | Today's KPI metrics |
| GET | `/api/live/gender-split` | Gender distribution (30 days) |
| GET | `/api/live/age-split` | Age group distribution (30 days) |
| GET | `/api/live/status-breakdown` | Enrollment status counts |
| GET | `/api/live/update-types` | Update request type breakdown |
| GET | `/api/live/regions` | All regions for filter dropdown |

### Past History
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/history/monthly-trend` | Monthly counts for a year |
| GET | `/api/history/regional-comparison` | Per-region totals in date range |
| GET | `/api/history/yearly-growth` | Year-over-year totals |
| GET | `/api/history/update-history` | Update breakdown in date range |

### Insights
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/insights/recommendations` | AI recommendations |
| GET | `/api/insights/biometric-quality` | Avg biometric quality scores |

### Anomalies
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/anomalies/list` | All anomaly records |
| GET | `/api/anomalies/detect-surges` | Real-time surge detection |

All endpoints (except login) require the `Authorization: Bearer <token>` header.

---

## Non-Functional Requirements Implemented

| Requirement | Implementation |
|-------------|----------------|
| Data security & privacy | JWT auth, bcrypt passwords, anonymized biometric |
| Large dataset performance | SQLAlchemy connection pool, aggregation views |
| Scalability | Modular router architecture, easy to add datasets |
| Data filtering | Region, time period, category filters on all endpoints |
| Report export | CSV export button on all table pages |
| Visualisation | Chart.js charts: doughnut, bar, line, stacked bar |
| Real-time metrics | Auto-refresh every 60 seconds on Live Stats tab |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML5/CSS3/JS, Chart.js 4.4 |
| Backend | Python 3.11, FastAPI 0.111 |
| Database | MySQL 8.0, SQLAlchemy ORM |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Fonts | Syne (display) + DM Sans (body) |
