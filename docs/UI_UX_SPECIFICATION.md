# UI/UX Specification & SOC Design System (v2.0.0-rc1)

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Tag**: `v2.0.0-rc1`  
**Frontend Framework**: React 18 + Vite + Tailwind CSS + Lucide Icons  

---

## 1. SOC Design Language & Semantic Color Palette

| Semantic Role | Color | Hex / Class | Meaning / Application |
| :--- | :--- | :--- | :--- |
| **Neutral / Background** | Slate / Zinc | `#0f172a` / `bg-slate-900` | Application shell, card surfaces, borders |
| **Information** | Blue | `#3b82f6` / `text-blue-400` | Cloudflare telemetry, `CF-Ray` tags, metadata |
| **Warning / Step-Up** | Amber / Yellow | `#f59e0b` / `text-amber-400` | Step-Up 2FA challenges, elevated velocity |
| **Review Required** | Orange | `#f97316` / `text-orange-400` | Medium risk ($40 \le \text{Score} < 75$) SOC reviews |
| **High-Risk / Blocked** | Red | `#ef4444` / `text-red-400` | Critical risk ($\text{Score} \ge 75$), token revocation |
| **Verified / Allowed** | Green | `#10b981` / `text-emerald-400`| Legitimate payments ($\text{Score} < 20$), verified actions |
| **Agent / Intelligence** | Purple / Indigo | `#8b5cf6` / `text-purple-400` | ReAct agent steps, threat intelligence matches |

---

## 2. 14 Operational Views Summary

1. **`/` (Landing & Overview)**: System executive summary, dual-threshold architecture overview, and quick links.
2. **`/dashboard` (Main SOC Dashboard)**: Top KPI metrics, response tier distribution, real-time risk feed.
3. **`/transactions` (Transaction Stream)**: Paginated, filterable, and searchable authorization stream with server-masked PANs.
4. **`/transactions/:id` (Flagship Investigation View)**: Deep-dive correlation view combining transaction details, CTI, Cloudflare signals, agent investigation timeline, policy authorization, and audit hash block.
5. **`/cards` (Card Exposure Intelligence)**: HMAC-SHA-256 card fingerprint database with compromise sources.
6. **`/tokens` (Token Intelligence & Vault)**: Token lifecycle management with zombie token detection flag.
7. **`/cases` (Security Case Management)**: SOC triage queue with status tabs (Open, Review, Resolved).
8. **`/agent` (Agent Activity & ReAct Timeline)**: Dynamic tool call traces with safe reasoning summary.
9. **`/threat-intelligence` (Threat Intelligence Center)**: Dark-web stealer log matches and paste feed telemetry.
10. **`/security` (Security Center)**: 9 security pillars with live status checks and key rotation status.
11. **`/security/data-protection` (Data Protection)**: Detailed 3-pillar cryptographic matrix (At Rest, In Transit, In Use) with interactive DLP sandbox.
12. **`/actions` (Action Center)**: History of automated and manual token revocations and Step-Up challenges.
13. **`/audit` (SHA-256 Hash Chain Ledger)**: Tamper-evident hash ledger with 1-click `Verify Chain Integrity` button.
14. **`/evaluation` (Reproducible Evaluation Screen)**: Frozen held-out test set benchmark metrics ($N=300$).
15. **`/demo` (Demo Control Center)**: 10 deterministic demo scenario cards and 1-click database reset button.
