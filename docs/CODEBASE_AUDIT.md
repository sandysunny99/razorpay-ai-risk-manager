# Codebase & Repository Structure Audit

**Date**: 2026-08-23T11:33:45+05:30  
**Status**: Clean Greenfield Implementation

---

## 1. Directory Tree & Module Map

```
RAZAORPAY AI/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── prompts.py          # Structured instructions & prompt boundaries
│   │   │   ├── risk_agent.py       # Autonomous Agent loop (Observe -> Audit)
│   │   │   └── tools.py            # Agent Tool Registry
│   │   ├── api/
│   │   │   ├── routes_audit.py     # /api/v1/audit/events
│   │   │   ├── routes_cards.py     # /api/v1/cards
│   │   │   ├── routes_cases.py     # /api/v1/cases
│   │   │   ├── routes_demo.py      # /api/v1/demo/*
│   │   │   ├── routes_risk.py      # /api/v1/risk/*
│   │   │   └── routes_tokens.py    # /api/v1/tokens/*
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic v2 BaseSettings
│   │   │   ├── database.py         # SQLAlchemy engine & session maker
│   │   │   └── security.py         # Luhn, HMAC fingerprinting, DLP
│   │   ├── db/
│   │   │   └── seed_data.py        # Seed dataset for demo scenarios
│   │   ├── engines/
│   │   │   ├── card_risk.py        # Card lifecycle & status engine
│   │   │   ├── exposure_correlation.py # Multi-feed threat correlation
│   │   │   ├── policy_engine.py    # Deterministic Guardrail Engine
│   │   │   ├── risk_scorer.py      # Multi-factor mathematical scoring
│   │   │   ├── token_risk.py       # Token risk & Zombie token detector
│   │   │   ├── transaction_risk.py # Deterministic amount/velocity/geo engine
│   │   │   └── verification_engine.py # ACT -> VERIFY -> RECALCULATE
│   │   ├── integrations/
│   │   │   └── razorpay_adapter.py # Payment Gateway Adapter
│   │   ├── models/
│   │   │   ├── entities.py         # SQLAlchemy DB Tables
│   │   │   └── schemas.py          # Pydantic Request/Response models
│   │   ├── threat_intel/
│   │   │   ├── base.py             # ThreatIntelProvider ABC
│   │   │   └── synthetic_provider.py # 9 offline testing scenarios
│   │   └── main.py                 # FastAPI Application Factory
│   ├── requirements.txt            # Python Dependencies
│   └── tests/
│       ├── test_e2e_agent.py       # Golden Scenario integration test
│       ├── test_policy.py          # Policy guardrail unit tests
│       ├── test_risk_engines.py    # Transaction, Card, Token, Zombie tests
│       └── test_security.py        # Luhn, HMAC, DLP unit tests
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AuditTrailTable.tsx # Immutable audit ledger table
│   │   │   ├── CardRiskTable.tsx   # Monitored cards table
│   │   │   ├── DemoScenarioTrigger.tsx # 1-Click Golden Scenario trigger
│   │   │   ├── Header.tsx          # Branding & safety status pills
│   │   │   ├── InvestigationTimeline.tsx # Real-time Agent Execution Timeline
│   │   │   ├── RiskOverviewCards.tsx # Executive metric cards
│   │   │   ├── SecurityCasesTable.tsx # Security case queue
│   │   │   └── ZombieTokenAlerts.tsx # Zombie token detection panel
│   │   ├── services/
│   │   │   └── api.ts              # REST API client
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript interfaces
│   │   ├── App.tsx                 # Main layout & SOC orchestration
│   │   └── index.css               # Tailwind CSS rules
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
├── docs/                           # Comprehensive Engineering Documentation
├── scripts/                        # Automation & seed scripts
├── .gitignore                      # Security & artifact exclusions
├── pytest.ini                      # Test runner configuration
└── README.md                       # Main product guide
```

---

## 2. Codebase Quality Findings

1. **Zero Duplicate Modules**: Every domain capability is encapsulated in a single authoritative module.
2. **Zero Dead Dependencies**: `requirements.txt` and `package.json` contain only essential production and test packages.
3. **No Raw Secrets in Repository**: `.env` is gitignored; fallback keys are strictly test/mock keys.
4. **Clean Layer Separation**: API routes $\rightarrow$ Service/Engines $\rightarrow$ Database/Adapters.
