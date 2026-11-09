# API Status Contract

| Condition | HTTP Status | Meaning |
|---|---|---|
| Replay | 401 | The payload is identified as a replay attack or has a stale timestamp. |
| Invalid HMAC | 401 | The provided HMAC signature does not match the payload. |
| Cross Tenant | 403 | The tenant ID in the headers does not match the merchant ID in the payload. |
| Sensitive Field | 422 | Sensitive-field injection is rejected during strict request validation (e.g., `card_pan`). |
