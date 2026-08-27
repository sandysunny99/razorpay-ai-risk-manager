# Razorpay Risk Manager Agent: Deployment & Operations Guide

## 1. Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### Step 1: Start the Backend
```bash
# From repository root
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload --port 8000
```
The backend initializes the SQLite database and seed data automatically on startup.

### Step 2: Start the Frontend SOC Dashboard
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173/` in your browser.

---

## 2. Docker & Container Deployment

### Dockerfile (Backend)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DRY_RUN=true
      - HMAC_SECRET_KEY=razorpay_prod_salt_secret
```
