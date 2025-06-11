"""
📰 NASDAQ News Alert Bot
Auteur: a4nD8 (Jordy Philippaerts)
Doel: Realtime alerts via Telegram voor impactvol marktnieuws m.b.t. NASDAQ/Big Tech
"""

import websocket
import json
import time
import threading
import os
from dotenv import load_dotenv
from telegram import Bot

# === Load .env secrets ===
load_dotenv()

FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# === Check op missende env vars ===
if not all([FINNHUB_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    print("❌ Eén of meerdere environment variabelen ontbreken.")
    print("📌 Controleer of je een geldig .env bestand hebt met FINNHUB_API_KEY, TELEGRAM_BOT_TOKEN en TELEGRAM_CHAT_ID.")
    exit(1)

# === Config ===
SYMBOLS = ['general', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'QQQ', 'NQ=F']
KEYWORDS = [
    'NASDAQ', 'NQ=F', 'QQQ', 'tech sector', 'rate hike', 'Federal Reserve', 'FOMC',
    'inflation', 'interest rate', 'recession', 'CPI', 'PPI', 'unemployment',
    'Treasury yield', 'AI bubble', 'chip shortage', 'semiconductor', 'earnings',
    'Apple', 'Tesla', 'Microsoft', 'Nvidia', 'Amazon', 'Meta', 'Google', 'Alphabet',
    'FAANG', 'Big Tech', 'SPAC', 'IPO', 'jobless claims'
]

sent_headlines = set()
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def send_alert(title, summary, url):
    if not summary:
        summary = 'Geen samenvatting beschikbaar.'

    msg = f"📰 <b>{title}</b>\n\n{summary}\n🔗 <a href=\"{url}\">Lees meer</a>"
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode='HTML', disable_web_page_preview=True)
        print(f"✅ Alert verzonden: {title}")
    except Exception as e:
        print(f"❌ Telegram-fout: {e}")

def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "news":
        for article in data.get("data", []):
            title = article.get('headline', '').strip()
            summary = article.get('summary', '').strip()
            url = article.get('url', '')
            combined = f"{title} {summary}".lower()

            if title in sent_headlines:
                continue

            if any(keyword.lower() in combined for keyword in KEYWORDS):
                send_alert(title, summary, url)
                sent_headlines.add(title)

def on_error(ws, error):
    print(f"❌ WebSocket fout: {error}")

def on_close(ws, close_status_code, close_msg):
    print("🔌 Verbinding verbroken. Herstart binnen 5 seconden...")
    time.sleep(5)
    start_socket()

def on_open(ws):
    print("🔗 Verbonden met Finnhub WebSocket.")
    ws.send(json.dumps({"type": "auth", "token": FINNHUB_API_KEY}))

    for symbol in SYMBOLS:
        ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))
        print(f"📥 Subscribed op: {symbol}")

def start_socket():
    ws = websocket.WebSocketApp(
        f"wss://ws.finnhub.io?token={FINNHUB_API_KEY}",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    threading.Thread(target=ws.run_forever, daemon=True).start()

if __name__ == "__main__":
    websocket.enableTrace(False)

    while True:
        try:
            print("🚀 NASDAQ WebSocket Alert Bot gestart.")
            start_socket()
            while True:
                time.sleep(60)
        except Exception as e:
            print(f"💥 Fout op hoofdniveau: {e}. Herstart binnen 5 seconden...")
            time.sleep(5)
