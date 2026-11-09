# Gate 13: Security React Dashboard

## Engineering Status
**IMPLEMENTED**

## Verification Status
**VERIFIED** (6 frontend tests passed, frontend build succeeds)

## Architecture
- **Framework**: React 18, Vite, TypeScript
- **Styling**: Tailwind CSS
- **Routing**: React Router (`/`, `/transaction`, `/audit`, `/health`)
- **API Strategy**: Strongly typed Axios client with environment variables (`VITE_API_BASE_URL`).

## Security Controls Verified
- **XSS Defense**: The `sanitizeHtmlToText` utility securely extracts text-only content, discarding executable tags like `<script>`.
- **DLP Sanitizer**: Active scrubber masks PAN patterns and explicit CVV injections natively in the React rendering tree to prevent UI leakage even if the backend errs.
- **Strict Visual Separation**: The UI strictly demarcates "AI ADVISORY" from "DETERMINISTIC POLICY DECISION" in separate bounded sections.
- **State Security**: Transaction data is intentionally held only in component memory (`useState`) and never exported to `localStorage` or `sessionStorage`.
- **Error Handling**: `500` errors are caught and transformed into safe consumer messages without raw backend stack-traces.
- **Provider Accuracy**: System Health explicitly labels unavailable AI providers as HTTP Contract Tested / Unavailable, declining to fabricate mock health statuses.

## Synthetic Data Policy
The frontend operates natively in `SYNTHETIC / DEMONSTRATION DATA MODE`. A persistent sticky banner warns the user, and individual transaction screens explicitly designate events as synthetic to prevent confusion with live Razorpay production data.

## Known Limitations
- The current build utilizes the HTTP-contract fallback behavior for AI providers (which return "UNAVAILABLE") because valid API integrations have not yet been executed with live credentials.
