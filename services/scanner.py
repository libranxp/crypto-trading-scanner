import logging
from db import supabase, TABLE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_auto_scan():
    logger.info("Starting auto scan...")

    # Example: list of symbols (replace with your logic)
    symbols = ["BTC", "ETH", "USDT", "SOL"]

    results = []
    for sym in symbols:
        try:
            # Fake scan data — replace with your real scan logic
            data = {
                "symbol": sym,
                "price": 0,  # replace with actual price fetch
                "status": "ok"
            }
            results.append(data)
        except Exception as e:
            logger.error(f"Error scanning {sym}: {e}")

    # If supabase client exists, save results
    if supabase:
        for item in results:
            try:
                supabase.table(TABLE).insert(item).execute()
            except Exception as e:
                logger.error(f"Error saving {item['symbol']} to Supabase: {e}")
    else:
        logger.info("Supabase not configured. Skipping DB save.")

    logger.info(f"Scan complete. Results: {results}")


if __name__ == "__main__":
    run_auto_scan()
