import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import SessionLocal, Base, engine
from app.db.seed_data import seed_initial_data

def main():
    print("[*] Resetting Database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    print("[*] Re-seeding Initial Demo State...")
    with SessionLocal() as db:
        seed_initial_data(db)
    print("[+] Reset Complete! Ready for fresh demo run.")

if __name__ == "__main__":
    main()
