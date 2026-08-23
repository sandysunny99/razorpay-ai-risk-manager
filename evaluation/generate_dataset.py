import json
import random
import hashlib
import os

SEED = 42
TOTAL_SAMPLES = 2000
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

random.seed(SEED)

def generate_record(idx: int, label: int) -> dict:
    txn_id = f"eval_{idx:04d}"
    merchant_id = random.choice(["merchant_demo_01", "merchant_demo_02", "merchant_demo_03"])
    cust_num = random.randint(1000, 9999)
    customer_id = f"cust_{cust_num}"
    card_suffix = f"{random.randint(1000, 9999)}"
    card_masked = f"**** **** **** {card_suffix}"
    card_fp = hashlib.sha256(f"salt_fp_{cust_num}_{card_suffix}".encode()).hexdigest()
    
    if label == 1:
        # Compromised / Fraudulent scenarios
        scenario_type = random.choice([
            "stealer_active_token",
            "zombie_token_exploit",
            "velocity_stuffing",
            "cross_border_high_val"
        ])
        
        if scenario_type == "stealer_active_token":
            amount = round(random.uniform(8000, 45000), 2)
            country = random.choice(["RU", "US", "NG", "VN", "UA", "BR"])
            customer_country = "IN"
            velocity = random.randint(3, 8)
            card_exposed = True
            exposure_conf = round(random.uniform(0.80, 0.99), 2)
            exposure_src = random.choice(["RedLine_Stealer_Dump", "Vidar_Log_Dump", "Telegram_Market"])
            token_active = True
            token_age = random.randint(10, 180)
            is_zombie = False
            card_expired = False
            device_new = True
            failed_attempts = random.randint(2, 6)

        elif scenario_type == "zombie_token_exploit":
            amount = round(random.uniform(2500, 20000), 2)
            country = random.choice(["IN", "US", "SG", "GB"])
            customer_country = "IN"
            velocity = random.randint(2, 5)
            card_exposed = random.choice([True, False])
            exposure_conf = round(random.uniform(0.60, 0.90), 2) if card_exposed else 0.0
            exposure_src = "Pastebin_Dump" if card_exposed else "None"
            token_active = True
            token_age = random.randint(200, 600)
            is_zombie = True
            card_expired = True
            device_new = random.choice([True, False])
            failed_attempts = random.randint(1, 4)

        elif scenario_type == "velocity_stuffing":
            amount = round(random.uniform(1000, 12000), 2)
            country = random.choice(["IN", "ID", "PH", "TH"])
            customer_country = "IN"
            velocity = random.randint(5, 12)
            card_exposed = True
            exposure_conf = round(random.uniform(0.70, 0.95), 2)
            exposure_src = "DarkWeb_Card_Forum"
            token_active = random.choice([True, False])
            token_age = random.randint(5, 60)
            is_zombie = False
            card_expired = False
            device_new = True
            failed_attempts = random.randint(3, 8)

        else: # cross_border_high_val
            amount = round(random.uniform(15000, 75000), 2)
            country = random.choice(["RU", "NG", "RO", "AE"])
            customer_country = "IN"
            velocity = random.randint(2, 4)
            card_exposed = True
            exposure_conf = round(random.uniform(0.85, 0.99), 2)
            exposure_src = "LummaC2_Stealer"
            token_active = True
            token_age = random.randint(15, 90)
            is_zombie = False
            card_expired = False
            device_new = True
            failed_attempts = random.randint(1, 3)

    else:
        # Legitimate / Clean scenarios (label = 0)
        scenario_type = random.choice([
            "standard_clean",
            "high_value_clean",
            "low_conf_exposure_clean",
            "inactive_token_clean"
        ])
        
        if scenario_type == "standard_clean":
            amount = round(random.uniform(150, 4500), 2)
            country = "IN"
            customer_country = "IN"
            velocity = 1
            card_exposed = False
            exposure_conf = 0.0
            exposure_src = "None"
            token_active = random.choice([True, False])
            token_age = random.randint(30, 400)
            is_zombie = False
            card_expired = False
            device_new = False
            failed_attempts = 0

        elif scenario_type == "high_value_clean":
            amount = round(random.uniform(15000, 65000), 2)
            country = "IN"
            customer_country = "IN"
            velocity = 1
            card_exposed = False
            exposure_conf = 0.0
            exposure_src = "None"
            token_active = True
            token_age = random.randint(60, 500)
            is_zombie = False
            card_expired = False
            device_new = False
            failed_attempts = 0

        elif scenario_type == "low_conf_exposure_clean":
            # Edge case: Weak threat feed signal, but legitimate payment
            amount = round(random.uniform(500, 3500), 2)
            country = "IN"
            customer_country = "IN"
            velocity = 1
            card_exposed = True
            exposure_conf = round(random.uniform(0.15, 0.35), 2) # Low confidence
            exposure_src = "Unverified_Paste"
            token_active = True
            token_age = random.randint(40, 250)
            is_zombie = False
            card_expired = False
            device_new = False
            failed_attempts = 0

        else: # inactive_token_clean
            amount = round(random.uniform(300, 2800), 2)
            country = "IN"
            customer_country = "IN"
            velocity = random.randint(1, 2)
            card_exposed = False
            exposure_conf = 0.0
            exposure_src = "None"
            token_active = False
            token_age = 0
            is_zombie = False
            card_expired = False
            device_new = False
            failed_attempts = random.choice([0, 1])

    return {
        "transaction_id": txn_id,
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "card_masked": card_masked,
        "card_fingerprint": card_fp,
        "amount": amount,
        "currency": "INR",
        "country": country,
        "customer_country": customer_country,
        "velocity_10m": velocity,
        "card_exposed": card_exposed,
        "exposure_confidence": exposure_conf,
        "exposure_source": exposure_src,
        "token_active": token_active,
        "token_age_days": token_age,
        "is_zombie_token": is_zombie,
        "card_expired": card_expired,
        "device_new": device_new,
        "failed_attempts_count": failed_attempts,
        "label": label
    }

def main():
    out_dir = os.path.dirname(__file__)
    os.makedirs(out_dir, exist_ok=True)
    
    # 75% negative (clean), 25% positive (compromised)
    num_pos = int(TOTAL_SAMPLES * 0.25)
    num_neg = TOTAL_SAMPLES - num_pos
    
    dataset = []
    for i in range(num_pos):
        dataset.append(generate_record(i + 1, label=1))
    for i in range(num_neg):
        dataset.append(generate_record(num_pos + i + 1, label=0))
        
    random.shuffle(dataset)
    # Re-assign transaction IDs sequentially
    for idx, row in enumerate(dataset):
        row["transaction_id"] = f"eval_{idx+1:04d}"
        
    train_end = int(TOTAL_SAMPLES * TRAIN_RATIO)
    val_end = train_end + int(TOTAL_SAMPLES * VAL_RATIO)
    
    train_data = dataset[:train_end]
    val_data = dataset[train_end:val_end]
    test_data = dataset[val_end:]
    
    # Write files
    for name, data in [("train.jsonl", train_data), ("validation.jsonl", val_data), ("test.jsonl", test_data)]:
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
        pos_cnt = sum(1 for x in data if x["label"] == 1)
        neg_cnt = len(data) - pos_cnt
        print(f"[+] Wrote {len(data)} records to {name} (Pos: {pos_cnt}, Neg: {neg_cnt})")

if __name__ == "__main__":
    main()
