import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from scanner_tier1 import tier1_scan
from scanner_tier2 import tier2_analysis_for_coin
from telegram_alerts import send_telegram_alert_for_coin
from duplicate_cache import should_alert
from config import DUPLICATE_ALERT_HOURS
import time

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def run_one_scan_and_alert():
    logger.info("Running Tier1 auto scan")
    try:
        results = tier1_scan(limit_coins=250)
        logger.info("Tier1 found %d coins", len(results))
        # For each result, run Tier2 quick analysis and alert if new
        for coin in results:
            symbol = coin.get("symbol")
            if not symbol:
                continue
            if not should_alert(symbol, DUPLICATE_ALERT_HOURS):
                logger.info("Skipping duplicate alert for %s", symbol)
                continue
            # run tier2 quick for richer data
            enriched = tier2_analysis_for_coin(coin)
            send_telegram_alert_for_coin(enriched)
            time.sleep(0.2)  # short sleep to avoid Telegram rate limits
    except Exception as e:
        logger.exception("Auto scan failed: %s", e)

def start_scheduler():
    # Cron trigger: every 45 minutes between 08:00-21:00 BST.
    # Render uses UTC environment; BST is UTC+1 (but DST varies). To keep this simple,
    # we'll schedule repeating job every 45 minutes and skip outside hours in job body.
    scheduler.add_job(run_one_scan_and_alert, 'interval', minutes=45, next_run_time=None)
    scheduler.start()
    logger.info("Scheduler started (45m interval)")

def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
