import requests
from config import *
from technical_indicators import calculate_rsi, calculate_ema_alignment, calculate_vwap_proximity, calculate_rvol
from sentiment_analysis import get_lunarcrush_sentiment, get_reddit_sentiment, get_santiment_sentiment, get_twitter_metrics
from catalyst_analysis import get_coinmarketcal_events, get_newsapi_news, get_cryptopanic_news, get_messari_news
from telegram_alerts import send_telegram_alert

def tier2_scan(symbols):
    results = []
    for symbol in symbols:
        price, volume, market_cap = 0, 0, 0
        # Try CoinGecko first
        try:
            params = {"vs_currency": "usd", "ids": symbol.lower()}
            resp = requests.get(f"{COINGECKO_API_URL}/coins/markets", params=params)
            data = resp.json()
            if data:
                price = data[0].get("current_price", 0)
                volume = data[0].get("total_volume", 0)
                market_cap = data[0].get("market_cap", 0)
        except Exception:
            # Fallback to CoinMarketCap
            try:
                headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY}
                resp = requests.get(f"{COINMARKETCAP_API_URL}/cryptocurrency/quotes/latest", params={"symbol": symbol}, headers=headers)
                data = resp.json()
                quote = data.get("data", {}).get(symbol, {}).get("quote", {}).get("USD", {})
                price = quote.get("price", 0)
                volume = quote.get("volume_24h", 0)
                market_cap = quote.get("market_cap", 0)
            except Exception:
                pass

        rsi = calculate_rsi(symbol)
        ema_aligned = calculate_ema_alignment(symbol)
        vwap_proximity = calculate_vwap_proximity(symbol, price)
        rvol = calculate_rvol(symbol)

        lunarcrush_sentiment = get_lunarcrush_sentiment(symbol)
        reddit_sentiment = get_reddit_sentiment()
        santiment_sentiment = get_santiment_sentiment(symbol)
        twitter_metrics = get_twitter_metrics(symbol)

        # Combine sentiment scores (simple average)
        sentiment_score = (lunarcrush_sentiment + reddit_sentiment + santiment_sentiment) / 3

        # Catalyst events
        coinmarketcal_events = get_coinmarketcal_events(symbol)
        newsapi_news = get_newsapi_news(symbol)
        cryptopanic_news = get_cryptopanic_news()
        messari_news = get_messari_news(symbol)

        # AI Score (example weighted average)
        ai_score = (rsi/100 + sentiment_score + rvol/10) / 3
        risk = 1 - ai_score

        coin_data = {
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "market_cap": market_cap,
            "rsi": rsi,
            "ema_aligned": ema_aligned,
            "vwap_proximity": vwap_proximity,
            "rvol": rvol,
            "sentiment_score": sentiment_score,
            "twitter_mentions": twitter_metrics["mentions"],
            "engagement_score": twitter_metrics["engagement_score"],
            "ai_score": ai_score,
            "risk": risk,
            "catalyst_events": coinmarketcal_events,
            "news": newsapi_news + cryptopanic_news + messari_news
        }

        # Send Telegram alert for Tier 2 results
        send_telegram_alert(coin_data)

        results.append(coin_data)

    return results
