# Edge security and secrets (deployment guide)

These controls live in front of, or beside, the API rather than inside it. Netvrio already rate-limits its
ingest endpoints (SlowAPI, `NETVRIO_RATE_LIMIT`), verifies every webhook signature, and sends a strict
Content-Security-Policy. The pieces below add defence in depth for a real deployment. None of them is
exercised by the test suite.

## WAF: Coraza or ModSecurity with the OWASP Core Rule Set

Both run the same [OWASP Core Rule Set](https://github.com/coreruleset/coreruleset) (Apache-2.0).
[Coraza](https://github.com/corazawaf/coraza) (Apache-2.0) is the simpler choice with Caddy:

```caddyfile
{
    order coraza_waf first
}

netvrio.example.com {
    coraza_waf {
        load_owasp_crs
        directives `
            Include @coraza.conf-recommended
            Include @crs-setup.conf.example
            Include @owasp_crs/*.conf
            SecRuleEngine On
            # Webhook bodies are signed JSON; keep the WAF from rewriting or blocking them on JSON quirks.
            SecRule REQUEST_URI "@beginsWith /integrations/" "id:1001,phase:1,pass,nolog,ctl:requestBodyProcessor=JSON"
        `
    }
    reverse_proxy 127.0.0.1:8000 {
        # The API rate-limits on the peer address; pass the client's real address through.
        header_up X-Real-IP {remote_host}
    }
}
```

Start in detection mode (`SecRuleEngine DetectionOnly`) for a week and tune false positives before enforcing.

## Abuse banning: CrowdSec

[CrowdSec](https://github.com/crowdsecurity/crowdsec) (MIT) reads the reverse-proxy logs and bans IPs that
repeatedly hit 401/429 on `/webhooks/*` or `/integrations/*`, using shared community blocklists.

## Secrets: OpenBao

Keep `WEBHOOK_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, `YOUPI_WEBHOOK_SECRET`, `EXPOSURE_FEED_SECRET` and
`FINGERPRINT_HMAC_SECRET` in [OpenBao](https://github.com/openbao/openbao) (MPL-2.0, the open-source fork of
Vault; HashiCorp Vault itself is now BUSL) and inject them as environment variables at start-up. Rotate any
key that appears in a log or a commit; Gitleaks in CI is there to catch the latter.

## Razorpay and PCI basics

- Never store full card numbers, CVV or expiry. Netvrio rejects raw PANs at ingress and stores fingerprints only.
- Use Razorpay Checkout and tokens to stay out of most PCI-DSS scope.
- Test-mode keys only in the prototype.
- HTTPS only; CORS limited to the dashboard origin (`CORS_ALLOWED_ORIGINS`).
- The LLM only explains. It never approves, refunds or blocks; the ML model can only send a payment to human review.
