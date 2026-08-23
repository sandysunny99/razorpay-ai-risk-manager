#!/usr/bin/env python3
"""
Razorpay AI Risk Manager: 1-Click Demo Reset Script

Resets runtime database tables (transactions, security cases, audit ledger, mock tokens)
to a pristine initial state without modifying frozen evaluation datasets.
"""

import sys
from pathlib import Path

sys.path.insert(0, ".")
sys.path.insert(0, "backend")

from app.core.database import engine, Base, SessionLocal
from app.db.seed_data import seed_initial_data
from scripts.release_guard import verify_test_set_hash

def reset_demo():
    print("=" * 65)
    print("RAZORPAY AI RISK MANAGER: 1-CLICK DEMO RESET")
    print("=" * 65)
    
    # 1. Verify frozen test set hash
    print("[1] Verifying frozen evaluation test set integrity...")
    if not verify_test_set_hash():
        print("[ERROR] Test set hash mismatch. Reset aborted.")
        sys.exit(1)

    # 2. Reset database schema and seed data
    print("[2] Resetting SQLite database tables & audit ledger...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        seed_initial_data(db)
        print("[3] Pristine demonstration seed data injected successfully.")
    finally:
        db.close()

    print("-" * 65)
    print("[SUCCESS] DEMO STATE RESET COMPLETE.")
    print("  • Golden Demo Scenario 1 (Stealer Dump + Zombie Token) is ready.")
    print("  • Scenario 2 (Clean Domestic Payment) is ready.")
    print("  • Scenario 3 (Step-Up 2FA Challenge) is ready.")
    print("=" * 65)

if __name__ == "__main__":
    reset_demo()
