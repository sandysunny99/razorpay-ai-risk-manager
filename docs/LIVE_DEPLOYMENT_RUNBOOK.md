# Razorpay AI Risk Manager: Live Deployment Runbook

**Repository**: `https://github.com/sandysunny99/razorpay-ai-risk-manager`  
**Verified Branch**: `main`  
**Verified Release**: `v2.0.0-rc2` (Commit `866b4f0`)  
**CI Status**: **`100% GREEN (Run 32817277172)`**  

---

## 1. Render Deployment Walkthrough

### Step 1: Connect Repository to Render
1. Navigate to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** $\rightarrow$ **Blueprint** (or **Web Service**).
3. Connect your GitHub account and select repository: `sandysunny99/razorpay-ai-risk-manager`.
4. Select Branch: **`main`**.
5. Render detects [render.yaml](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/render.yaml) automatically:
   - **Runtime**: Docker (`Dockerfile`)
   - **Plan**: Starter / Standard
   - **Region**: Singapore (`sin`)
   - **Health Check Path**: `/health`

### Step 2: Configure Environment Secrets in Render Dashboard
Set the following environment variables under **Environment**:

| Variable Name | Required / Optional | Description | Recommended Value |
| :--- | :--- | :--- | :--- |
| `APP_MODE` | **Required** | Operational mode | `demo` or `production` |
| `DRY_RUN` | **Required** | Gateway safety barrier | `true` |
| `HMAC_SECRET_KEY` | **Required** | HMAC card fingerprinting key | *(Render auto-generates or 32+ char secret)* |
| `MASTER_ENCRYPTION_KEY` | **Required** | AES-256-GCM field encryption key | *(Render auto-generates or 32-byte urlsafe-b64)* |
| `DATABASE_URL` | **Required** | Persistence layer | `sqlite:///./risk_management.db` |
| `RAZORPAY_KEY_ID` | Optional | Razorpay Dashboard Test Key | `rzp_test_...` |
| `RAZORPAY_KEY_SECRET`| Optional | Razorpay Test Webhook Secret | `...` |
| `CLOUDFLARE_API_TOKEN`| Optional | Cloudflare API token | `...` |

### Step 3: Trigger Deploy & Obtain Origin URL
Click **Apply** or **Create Web Service**. Render builds the multi-stage Docker container:
1. Node 20 builds React + Vite frontend SPA bundle into `/app/frontend/dist`.
2. Python 3.12 installs backend dependencies and starts Uvicorn on port 8000.
3. Render queries `GET /health` and marks the deployment **Live**.

---

## 2. Cloudflare Custom Domain & Edge Proxy Configuration

### Step 1: Add Custom Hostname in Cloudflare
1. Go to Cloudflare Dashboard $\rightarrow$ Select your DNS Zone.
2. Navigate to **DNS** $\rightarrow$ **Records** $\rightarrow$ **Add record**:
   - **Type**: `CNAME`
   - **Name**: `risk` (or `@` / your preferred subdomain)
   - **Target**: `razorpay-risk-manager.onrender.com` (your actual Render service URL)
   - **Proxy status**: **Proxied (Orange Cloud)**

### Step 2: SSL / TLS Encryption Mode
1. In Cloudflare, navigate to **SSL/TLS** $\rightarrow$ **Overview**.
2. Select **Full (Strict)** to guarantee end-to-end encryption between Cloudflare edge and Render.
3. Under **Edge Certificates**, enable **Always Use HTTPS** and **Minimum TLS Version: TLS 1.3**.

### Step 3: Configure Edge WAF & Rate Limiting Rules
1. **WAF Custom Rules**:
   - Rule Name: `Protect Sensitive Risk API`
   - Expression: `(http.request.uri.path contains "/api/v1/zombie-cards/tokens" and http.request.method eq "POST")`
   - Action: `Managed Challenge` (for bot score $< 30$)
2. **Rate Limiting Rules**:
   - Rule Name: `Protect Webhooks & Auth`
   - Path: `/api/v1/webhooks/*` and `/api/v1/auth/*`
   - Threshold: `100 requests per 1 minute`
   - Action: `Block (429)`

---

## 3. Post-Deployment Verification Protocol

Once the public URL is live, run the verification script:
```bash
python scripts/test_public_deployment.py --url https://<YOUR_RENDER_OR_CLOUDFLARE_URL>
```

The script validates:
- `GET /health` $\rightarrow$ HTTP 200 (`status: healthy`)
- `GET /api/v1/health/dependencies` $\rightarrow$ HTTP 200 (All core subsystems UP)
- `GET /api/v1/zombie-cards` $\rightarrow$ HTTP 200 (Active zombie cards & tokens)
- `POST /api/v1/webhooks/razorpay` $\rightarrow$ Mandatory HMAC-SHA256 signature verification & deduplication
- `GET /api/v1/security/data-protection` $\rightarrow$ AES-256-GCM & DLP scrubber validation
