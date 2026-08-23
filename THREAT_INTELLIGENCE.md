# Razorpay Risk Manager Agent: Threat Intelligence Architecture

## 1. Threat Intelligence Provider Abstraction

Threat intelligence sources vary from commercial feeds to dark web scrapers and internal breach lakes. To prevent vendor lock-in and enable offline testing, the system provides a clean abstract interface:

```python
class ThreatIntelProvider(ABC):
    @abstractmethod
    async def search_card_fingerprint(self, card_fingerprint: str) -> List[ExposureMatch]: ...
    
    @abstractmethod
    async def search_bin_exposure(self, bin_number: str) -> List[ExposureMatch]: ...
    
    @abstractmethod
    async def search_email_exposure(self, email: str) -> List[ExposureMatch]: ...
```

---

## 2. Supported Intelligence Sources

1. **`SyntheticThreatIntelProvider` (Default / Offline)**:
   - Built specifically for reproducible testing and offline hackathon evaluation.
   - Provides deterministic match fixtures for 9 core testing scenarios.
2. **Stealer Log Monitors**:
   - Integrates structured feeds originating from infostealer malware families (RedLine, Racoon, Vidar, LummaC2).
   - Extracts browser-saved card data, compromised system tags, and timestamp metadata.
3. **Underground Paste & Breach Dumps**:
   - Monitors paste sites and breach aggregators for bulk card dumps.
4. **BIN Compromise Alerts**:
   - Tracks issuer-level compromise rates to alert when entire card ranges are under active attack.

---

## 3. The 9 Core Test Scenarios

| Scenario # | Profile Name | Fingerprint Match | Token State | Risk Expectation | Remediation Policy |
|---|---|---|---|---|---|
| **Scenario 1** | Clean Card | None | Active | $0 / 100$ (LOW) | Monitor |
| **Scenario 2** | Exposed Card | Single paste dump | Inactive | $45 / 100$ (MEDIUM) | Monitor / Log |
| **Scenario 3** | High-Confidence Exposure | RedLine stealer log ($0.96$) | Active | $94 / 100$ (CRITICAL) | `AUTO_EXECUTE` Revoke Token |
| **Scenario 4** | Low-Confidence Signal | Unverified dump ($0.45$) | Active | $35 / 100$ (MEDIUM) | Enhanced Monitoring |
| **Scenario 5** | Duplicate Exposure | Same dump repeated | Active | Deduped into 1 alert | Standard policy |
| **Scenario 6** | Multi-Source Match | Stealer + DarkMarket paste | Active | Elevated confidence | Priority escalation |
| **Scenario 7** | Expired Card Exposure | Breach dump match | None | $20 / 100$ (LOW) | Card replacement closed |
| **Scenario 8** | Exposed Card + Active Token | Stealer dump match | Active token | $80 / 100$ (CRITICAL) | Revoke token |
| **Scenario 9** | Exposed + Suspicious Txn | Stealer + ₹18,500 Moscow | Active token | $94 / 100$ (CRITICAL) | Revoke token $\rightarrow$ Drop to 21 |
