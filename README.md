# Razorpay AI Risk Manager

[![GitHub license](https://img.shields.io/github/license/sandysunny99/razorpay-ai-risk-manager)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/sandysunny99/razorpay-ai-risk-manager)](https://github.com/sandysunny99/razorpay-ai-risk-manager/stargazers)

## Phase 1 – Supply‑Chain Audit & Metrics

This repository provides a **proof‑of‑concept risk engine** for Razorpay transaction monitoring. In Phase 1 we:

- Ran a full dependency audit (npm audit, pip audit).
- Measured baseline test runtimes and output sizes.
- Generated a complete list of all repository files (`all_files_list.txt`).
- Integrated **Context Mode** (semantic indexing) and recorded its runtime.

### Documentation

- **Baseline metrics** – `docs/BASELINE_METRICS.md`
- **Post‑Context‑Mode metrics** – `docs/POST_CONTEXT_MODE_METRICS.md`
- Architecture overview, risk‑decision graph, and other analyses are available under the `docs/` folder.

### Quick start

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
npm ci

# Run unit tests (baseline)
pytest -q

# Run Context‑Mode integration
node dev/context-mode/cli.bundle.mjs --path sandbox
```

For detailed insights, refer to the linked docs above.
