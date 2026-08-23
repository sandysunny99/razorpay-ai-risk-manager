# Cloudflare Edge Perimeter Deployment Specification

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Tag**: `v2.0.0-rc1`  
**Operational Status**: **SIMULATED / ADAPTER_VALIDATED**  

---

## 1. Cloudflare Perimeter Integration Architecture

```
                       INCOMING CLIENT TRAFFIC
                                 │
                                 ▼
                     CLOUDFLARE EDGE PERIMETER
             ┌────────────────────────────────────────┐
             │ • TLS 1.3 / Strict HTTPS Termination   │
             │ • Managed WAF Inspection Rules         │
             │ • 1-99 Bot Management Classification   │
             │ • Token-Bucket Rate Limiting (100/min) │
             │ • Unique CF-Ray ID Request Tracking   │
             └───────────────────┬────────────────────┘
                                 │ Injected Headers
                                 ▼
                     FASTAPI GATEWAY ADAPTER
             (`backend/app/integrations/cloudflare_adapter.py`)
```

---

## 2. Telemetry Normalization & Bot Classification

| Header / Field | Normalized Parameter | Value Range / Taxonomy | Purpose |
| :--- | :--- | :--- | :--- |
| `CF-Ray` | `ray_id` | 16-character hex | Distributed request tracing across systems |
| `CF-IPCountry` | `client_country` | ISO 3166-1 alpha-2 | Foreign geographic anomaly detection |
| `CF-Bot-Score` | `bot_score` | 1: `VERIFIED_BOT`<br>2–29: `LIKELY_AUTOMATED`<br>30–99: `LIKELY_HUMAN`<br>`UNKNOWN` | Automated scraping and credential stuffing defense |
| `CF-WAF-Action` | `waf_action` | `ALLOW`, `BLOCK`, `CHALLENGE` | Perimeter attack mitigation telemetry |
