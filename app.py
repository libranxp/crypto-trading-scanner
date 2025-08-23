import logging
import time
from datetime import datetime
from scheduler import run_scheduler
from telegram_alerts import send_telegram_message

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    logging.info("🚀 Crypto Scanner Service Starting...")

    try:
        run_scheduler()
    except Exception as e:
        logging.error(f"❌ Scanner crashed: {e}")
        send_telegram_message(f"❌ Scanner crashed: {e}")
        time.sleep(10)
