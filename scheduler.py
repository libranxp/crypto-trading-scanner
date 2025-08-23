import logging
import time
from datetime import datetime
import pytz
from config import START_HOUR, END_HOUR, SCAN_INTERVAL_MINUTES, TIMEZONE
from scanner_tier1 import run_tier1_scan
from scanner_tier2 import run_tier2_scan
from telegram_alerts import send_telegram_message

tz = pytz.timezone(TIMEZONE)

def run_scheduler():
    last_run = None
    while True:
        now = datetime.now(tz)
        if START_HOUR <= now.hour < END_HOUR:
            if not last_run or (now - last_run).seconds >= SCAN_INTERVAL_MINUTES * 60:
                logging.info(f"🕒 Running scan at {now}")
                try:
                    candidates = run_tier1_scan()
                    filtered = run_tier2_scan(candidates)
                    if filtered:
                        for coin in filtered:
                            send_telegram_message(f"✅ {coin['symbol']} passed filters: {coin}")
                    else:
                        logging.info("No coins matched criteria this cycle.")
                except Exception as e:
                    logging.error(f"Error in scan cycle: {e}")
                    send_telegram_message(f"⚠️ Error in scan cycle: {e}")
                last_run = now
        time.sleep(60)
