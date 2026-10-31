# MediRisk 2.0 — AI-Powered Multi-Disease Risk Assessment System

> **Project Type:** Research & Academic Health Risk Assessment Prototype  
> **Current Phase:** Phase 2 — Project Initialization  
> **Status:** Active Development Baseline  

---

## Overview

**MediRisk 2.0** is an academic and research-oriented full-stack healthcare risk-assessment platform. The system leverages state-of-the-art **Tabular Foundation Models** (specifically **TabPFN 9.0.0** and **TabICLv2 2.2.0**) to evaluate non-diagnostic risk profiles across 10 disease categories based on patient clinical, lifestyle, and demographic inputs.

### Supported Initial Diseases (Under Prototype Study)
1. Diabetes
2. Heart Disease
3. Stroke
4. Asthma
5. Chronic Kidney Disease
6. Liver Disease
7. Parkinson's Disease
8. Breast Cancer
9. Lung Cancer
10. Hypertension

---

## Important Safety & Clinical Disclaimer

> [!WARNING]  
> **MediRisk 2.0 is an educational and research prototyping tool only. It does NOT provide medical diagnoses, clinical determinations, or treatment plans.**  
> All risk categories (<30% Low Risk, 30–70% Moderate Risk, >70% High Risk) and recommendations are application-level prototype outputs generated from synthetic research datasets and must **NEVER** replace professional medical advice or clinical evaluation.

---

## Monorepo Architecture Stack

- **Frontend**: Next.js `16.3.6` (App Router), React `19.3.0`, TypeScript `5.6.2`, Tailwind CSS `4.3.3`, React Hook Form `7.53.0`, Zod `3.23.8`, Zustand `4.5.5`, TanStack Query `5.56.2`, Recharts `2.12.7`.
- **Backend API**: FastAPI `0.115.0`, Python `3.12.4`, Pydantic `2.13.5`, SQLAlchemy `2.0.35` (Asyncio), asyncpg `0.29.0`, Alembic `1.13.3`.
- **Security**: `pwdlib[argon2]` `0.2.0` (Argon2id password hashing) + `PyJWT[crypto]` `2.9.0` (Stateless JWT token handling).
- **ML Foundation Layer**: PyTorch `2.14.0` (CPU-First), TabPFN `9.0.0`, TabICLv2 `2.2.0`, scikit-learn `1.5.2`, SHAP `0.46.0`.
- **Infrastructure**: PostgreSQL `16.4` (Relational & JSONB data store) + Redis `7.4-alpine` (Session cache & rate-limiting store).

---

## Directory Hierarchy

```
medi-risk-2.0/
├── frontend/         # Next.js 16.3.6 App Router application
├── backend/          # FastAPI Python 3.12 async backend server
├── ml/               # Tabular foundation model architecture & experiment workflows
├── database/         # PostgreSQL migration & database seed management
├── infrastructure/   # Docker Compose configurations & environment scripts
├── docs/             # Technical specifications & academic paper drafts
└── tests/            # Shared integration & E2E Playwright test suites
```

---

## Getting Started (Phase 2 Local Setup)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

### 2. Infrastructure Setup (Docker Compose)
```bash
docker-compose up -d
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Synthetic Data Notice

MediRisk 2.0 uses **synthetic clinical datasets (~5,000 records per disease)** engineered strictly for software architecture benchmarking and research prototyping. Synthetic data does not equal clinically validated patient data.
