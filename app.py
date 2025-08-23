import logging
import time
from datetime import datetime, timedelta
from scanner_tier1 import tier1_scan
from scanner_tier2 import tier2_scan
from telegram_alerts import send_telegram_alert
from config import TIER1_INTERVAL_MINUTES, SCAN_START_HOUR, SCAN_END_HOUR

logging.basicConfig(level=logging.INFO)

def run_scanner():
    while True:
        now = datetime.utcnow() + timedelta(hours=1)  # BST offset
        if SCAN_START_HOUR <= now.hour <= SCAN_END_HOUR:
            logging.info("Running Tier1 scan...")
            tier1_symbols = tier1_scan()
            if tier1_symbols:
                logging.info(f"Tier1 found {len(tier1_symbols)} symbols, running Tier2...")
                tier2_alerts = tier2_scan(tier1_symbols)
                logging.info(f"Tier2 alerts: {len(tier2_alerts)}")
        time.sleep(TIER1_INTERVAL_MINUTES*60)

if __name__ == "__main__":
    logging.info("🚀 Crypto Scanner Service Starting...")
    try:
        run_scanner()
    except Exception as e:
        logging.error(f"❌ Scanner crashed: {e}")
        send_telegram_alert({"symbol":"SYSTEM","ai_score":0,"catalysts":f"Scanner crashed: {e}","twitter":{"mentions":0}})
        time.sleep(10)
