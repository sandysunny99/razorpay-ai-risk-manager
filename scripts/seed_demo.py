import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import SessionLocal, Base, engine
from app.db.seed_data import seed_initial_data

def main():
    print("[*] Initializing Database Schema...")
    Base.metadata.create_all(bind=engine)
    
    print("[*] Seeding Razorpay Risk Manager Demo Dataset...")
    with SessionLocal() as db:
        seed_initial_data(db)
    print("[+] Demo Data Seeding Complete!")

if __name__ == "__main__":
    main()
