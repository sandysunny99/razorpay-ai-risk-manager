from typing import Any, List
import uuid


class EvidenceItem:
    def __init__(self, description: str):
        self.description = description

class EvidencePackage(dict):
    def __init__(self, items: List[EvidenceItem], evidence_id: str):
        super().__init__()
        self.items = items
        self.evidence_id = evidence_id
        self["evidence_id"] = evidence_id

class EvidenceBuilder:
    def build(self, evidence_input: dict, risk_factors: list, zombie_assessment: Any) -> EvidencePackage:
        items = []
        if risk_factors:
            for factor in risk_factors:
                if isinstance(factor, dict):
                    items.append(EvidenceItem(f"Risk factor: {factor.get('reason')}"))
                elif hasattr(factor, 'reason'):
                    items.append(EvidenceItem(f"Risk factor: {factor.reason}"))
        if zombie_assessment and hasattr(zombie_assessment, 'signals') and zombie_assessment.signals:
            for signal in zombie_assessment.signals:
                if isinstance(signal, dict):
                    items.append(EvidenceItem(f"Zombie signal: {signal.get('description')}"))
                elif hasattr(signal, 'description'):
                    items.append(EvidenceItem(f"Zombie signal: {signal.description}"))
        return EvidencePackage(items=items, evidence_id=f"ev_{uuid.uuid4().hex[:8]}")
