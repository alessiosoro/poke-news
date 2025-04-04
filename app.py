import os
import time
import json
import hashlib
import threading
from bs4 import BeautifulSoup
import requests
from flask import Flask, send_file

app = Flask(__name__)

URL = "https://www.pokeguardian.com/articles/news-archive"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SENT_HASHES = set()
FIRST_RUN = not os.path.exists("first_run.flag")

def hash_news(title):
    return hashlib.md5(title.encode("utf-8")).hexdigest()

def fetch_news():
    try:
        res = requests.get(URL, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        news_blocks = soup.select(".sqs-block-content h3")
        links = soup.select(".sqs-block-content h3 a")
        
        news_items = []
        for h3, a in zip(news_blocks, links):
            title = h3.text.strip()
            link = a["href"]
            if not link.startswith("http"):
                link = "https://www.pokeguardian.com" + link
            news_items.append((title, link))
        return news_items
    except Exception as e:
        print("⚠️ Errore nel recupero delle news:", e)
        return []

def save_as_html(news_list):
    with open("news.html", "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <title>Ultime News Pokémon</title>
  <style>
    body { font-family: sans-serif; padding: 20px; background: #fafafa; }
    h1 { color: #006cff; }
    .news { margin-bottom: 20px; }
    .news a { color: #222; text-decoration: none; font-weight: bold; }
    .news a:hover { text-decoration: underline; }
    .news em { font-size: 0.9em; color: gray; }
  </style>
</head>
<body>
  <h1>📰 Ultime News da PokéGuardian</h1>
""")
        for item in news_list:
            f.write(f"""<div class="news">
  <a href="{item['link']}" target="_blank">{item['title']}</a><br>
  <em>Fonte: PokéGuardian</em>
</div>\n""")
        f.write("</body></html>")

def save_as_json(news_list):
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)

def run_scraper():
    global FIRST_RUN
    while True:
        print("🔎 Avvio scraping...\n")
        news = fetch_news()
        to_send = []

        if FIRST_RUN:
            print("🚀 Prima esecuzione: salvo prime 4 news.")
            for title, link in news[:4]:
                h = hash_news(title)
                if h not in SENT_HASHES:
                    to_send.append({"title": title, "link": link})
                    SENT_HASHES.add(h)
            with open("first_run.flag", "w") as f:
                f.write("done")
            FIRST_RUN = False
        else:
            for title, link in news:
                h = hash_news(title)
                if h not in SENT_HASHES:
                    if any(k in title.lower() for k in ["scarlet", "violet", "booster", "promo", "rocket", "destined", "rivals", "terastal"]):
                        to_send.append({"title": title, "link": link})
                        SENT_HASHES.add(h)

        if to_send:
            print(f"📤 Salvate {len(to_send)} news nuove.")
            save_as_html(to_send)
            save_as_json(to_send)
        else:
            print("⏸ Nessuna nuova notizia da salvare.")
        print("⏳ Attesa 1 minuto...\n")
        time.sleep(60)

@app.route("/")
def index():
    return send_file("news.html")

@app.route("/news.json")
def json_news():
    return send_file("news.json")

if __name__ == "__main__":
    threading.Thread(target=run_scraper).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
