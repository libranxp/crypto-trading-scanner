import time
import threading
from datetime import datetime, timedelta
from scanner_tier1 import tier1_scan
from scanner_tier2 import tier2_scan

BST_OFFSET = 1  # BST = UTC+1

def is_bst_active_hours():
    now_utc = datetime.utcnow()
    now_bst = now_utc + timedelta(hours=BST_OFFSET)
    return 8 <= now_bst.hour < 21

def auto_scan_loop():
    while True:
        if is_bst_active_hours():
            print("Running Tier 1 Auto Scan...")
            watchlist = tier1_scan()
            print(f"Tier 1 found {len(watchlist)} coins.")
            # Optionally trigger Tier 2 for top coins or events
        else:
            print("Outside active hours, sleeping...")
        time.sleep(45 * 60)  # 45 minutes

def manual_scan(symbols):
    print("Running Tier 2 Manual Scan...")
    results = tier2_scan(symbols)
    print(f"Tier 2 scan complete: {len(results)} results.")
    return results

# To start auto scan in background:
# threading.Thread(target=auto_scan_loop, daemon=True).start()
