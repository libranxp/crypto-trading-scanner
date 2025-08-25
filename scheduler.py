# scheduler.py
from services.scanner import scan_and_alert

if __name__ == "__main__":
    res = scan_and_alert()
    print(f"Alerts sent (if any): {len(res)}")
