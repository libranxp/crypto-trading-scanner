# scanner_tier1.py
from services.scanner import run_auto_scan

if __name__ == "__main__":
    rows = run_auto_scan()
    print(f"Tier-1 done: {len(rows)} candidates.")
