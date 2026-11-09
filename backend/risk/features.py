from typing import Any, Dict


def extract_features(transaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts features for deterministic risk engine.
    """
    features = {}
    features['amount'] = transaction_data.get('amount', 0.0)
    features['merchant_id'] = transaction_data.get('merchant_id', 'unknown')
    features['customer_id'] = transaction_data.get('customer_id', 'unknown')

    # Normally we would query previous events to get velocity
    features['velocity_1h'] = transaction_data.get('velocity_1h', 1)  # Stub
    return features
