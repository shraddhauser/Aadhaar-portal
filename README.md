# Aadhaar Analytics Portal

A modern full-stack analytics and monitoring platform for Aadhaar enrollment and update operations, providing real-time insights, data visualization, API-driven analytics, and administrative monitoring capabilities.

---

## Overview

The Aadhaar Analytics Portal is designed to help administrators monitor enrollment activities, track demographic trends, analyze update requests, and generate operational insights from Aadhaar-related datasets.

The platform combines:

* FastAPI Backend Services
* React Frontend Dashboard
* SQLite / SQLAlchemy Data Layer
* REST APIs
* Authentication & Authorization
* Analytics and Reporting Engine
* Health Monitoring Utilities

---

## Key Features

### Dashboard Analytics

* Total Aadhaar Enrollments
* Daily Enrollment Statistics
* Update Request Tracking
* Region-wise Analytics
* Age Group Distribution
* Gender Distribution
* Historical Trend Analysis

### User Management

* Secure Login System
* JWT Authentication
* Role-Based Access Control
* Session Management

### Data Management

* Enrollment Records
* Aadhaar Update Requests
* Historical Analytics
* Data Validation
* Audit Logging

### Monitoring & Health Checks

* API Health Monitoring
* Frontend Availability Checks
* Database Integrity Validation
* Automated Diagnostics

### Reporting

* Daily Reports
* Monthly Reports
* Exportable Analytics
* Historical Trend Reports

---

# System Architecture

```text
┌─────────────────────┐
│   React Frontend    │
│     Port : 3000     │
└──────────┬──────────┘
           │ REST API
           ▼
┌─────────────────────┐
│   FastAPI Backend   │
│     Port : 8000     │
└──────────┬──────────┘
           │ SQLAlchemy
           ▼
┌─────────────────────┐
│ SQLite Database     │
│ aadhaar_analytics.db│
└─────────────────────┘
```

---

# Technology Stack

## Frontend

* React.js
* HTML5
* CSS3
* JavaScript
* Chart.js

## Backend

* FastAPI
* Python 3.11+
* SQLAlchemy
* Pydantic

## Database

* SQLite
* SQLAlchemy ORM

## Authentication

* JWT Tokens
* Password Hashing

## DevOps

* GitHub Actions
* Docker
* Automated Testing

---

# Project Structure

```text
aadhaar-portal/
│
├── backend/
│   ├── app/
│   ├── api/
│   ├── models/
│   ├── services/
│   ├── database/
│   ├── middleware/
│   └── tests/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── assets/
│   └── tests/
│
├── scripts/
│
├── docs/
│
├── docker/
│
├── .github/
│   └── workflows/
│
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/your-username/aadhaar-portal.git

cd aadhaar-portal
```

## Create Virtual Environment

```bash
python -m venv .venv
```

### Windows

```powershell
.\.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
source .venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Configuration

Create a `.env` file.

```env
DATABASE_URL=sqlite:///aadhaar_analytics.db

API_HOST=127.0.0.1
API_PORT=8000

FRONTEND_URL=http://127.0.0.1:3000

SECRET_KEY=your_secret_key

ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

# Running the Application

## Backend

```bash
uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Swagger Documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend

```bash
npm install

npm start
```

Frontend URL:

```text
http://127.0.0.1:3000
```

---

# Testing

## Run All Tests

```bash
pytest
```

## Backend Smoke Test

```bash
python scripts/smoke_test.py
```

## Frontend Availability Check

```bash
python scripts/check_frontend.py
```

## Database Validation

```bash
python scripts/check_db_dates.py
```

## API Validation

```bash
python scripts/check_api_data.py
```

---

# API Endpoints

## Authentication

```http
POST /api/auth/login
POST /api/auth/register
POST /api/auth/logout
```

## Analytics

```http
GET /api/dashboard
GET /api/analytics/live
GET /api/analytics/history
```

## Health

```http
GET /health
GET /docs
```

---

# Security Features

* JWT Authentication
* Password Hashing
* Input Validation
* SQL Injection Protection
* API Rate Limiting
* Secure Environment Variables

---

# CI/CD Pipeline

GitHub Actions automatically performs:

* Code Quality Checks
* Unit Testing
* API Validation
* Dependency Verification
* Build Validation

Workflow:

```text
Push → Test → Build → Deploy
```

---

# Future Enhancements

## Phase 1

* PostgreSQL Migration
* Redis Caching
* API Rate Limiting

## Phase 2

* AI-powered Analytics
* Predictive Enrollment Forecasting
* Advanced Reporting

## Phase 3

* Kubernetes Deployment
* Cloud Storage Integration
* Multi-Region Scalability

---

# Performance Improvements

* Database Indexing
* Query Optimization
* Response Caching
* Background Job Processing

---

# Monitoring

* Application Health Checks
* API Response Monitoring
* Database Diagnostics
* Error Tracking

---

# Contributors

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Open a Pull Request

---

# License

This project is currently unlicensed.

For public release, add an appropriate license such as:

* MIT License
* Apache 2.0 License
* GPL v3

---

# Author

Developed as a modern Aadhaar Analytics and Monitoring Platform demonstrating:

* Full Stack Development
* FastAPI Backend Engineering
* React Frontend Development
* Database Design
* API Development
* Software Testing
* DevOps Practices
