import time
import threading
from flask import Flask, send_file
from requests_html import HTMLSession
from datetime import datetime

app = Flask(__name__)
session = HTMLSession()

NEWS_FILE = "news.html"
KEYWORDS = [
    "card", "cards", "pokémon card", "expansion", "booster", "set", "deck",
    "TCG", "trading card", "promo", "Rocket", "Prismatiche", "Terastal",
    "Rivali", "Predestinati", "Destined", "Rivals"
]

# Funzione di scraping per un sito
def fetch_site(url, source_name, container_selector, title_selector, link_selector):
    print(f"🔍 Scansione {source_name}...")
    results = []
    try:
        r = session.get(url)
        r.html.render(timeout=20, sleep=2)
        elements = r.html.find(container_selector)
        for el in elements[:10]:  # controlliamo i primi 10 per sicurezza
            title_el = el.find(title_selector, first=True)
            link_el = el.find(link_selector, first=True)

            if not title_el or not link_el:
                continue

            title = title_el.text.strip()
            link = link_el.attrs.get("href", "").strip()

            if not title or not link:
                continue

            if not link.startswith("http"):
                link = url.rstrip("/") + "/" + link.lstrip("/")

            if any(k.lower() in title.lower() for k in KEYWORDS):
                results.append({
                    "title": title,
                    "link": link,
                    "source": source_name
                })

            if len(results) >= 3:
                break

    except Exception as e:
        print(f"⚠️ Errore durante lo scraping di {source_name}: {e}")
    return results

# Funzione principale
def fetch_all_news():
    all_news = []

    all_news += fetch_site(
        "https://www.pokeguardian.com/articles/news-archive",
        "PokeGuardian",
        ".article-container",
        ".article-title", ".article-title a"
    )

    all_news += fetch_site(
        "https://www.pokebeach.com/news",
        "PokeBeach",
        ".post", "h2", "h2 a"
    )

    all_news += fetch_site(
        "https://www.pokemon.com/us/pokemon-news/",
        "Pokemon USA",
        ".news-article", ".news-article-title", "a"
    )

    all_news += fetch_site(
        "https://www.pokemon.co.jp/info/cat_card/",
        "Pokemon Japan",
        ".news-list__element", ".news-list__title", "a"
    )

    return all_news[:12]  # massimo 3 news per 4 fonti

# Genera l'HTML finale
def save_news_html(news):
    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        f.write("<html><head><meta charset='UTF-8'><title>News Pokémon TCG</title></head><body>")
        f.write("<h1>Ultime notizie carte Pokémon</h1><ul>")
        for item in news:
            f.write(f"<li><strong>{item['source']}</strong>: <a href='{item['link']}' target='_blank'>{item['title']}</a></li>")
        f.write("</ul><p>Aggiornato: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "</p>")
        f.write("</body></html>")
    print("✅ File news.html aggiornato!")

# Thread scraping continuo
def run_scraper():
    while True:
        print("🔄 Avvio scraping globale...")
        all_news = fetch_all_news()
        if all_news:
            save_news_html(all_news)
        else:
            print("⚠️ Nessuna news valida trovata.")
        time.sleep(300)  # 5 minuti

# Flask
@app.route("/")
def index():
    return send_file(NEWS_FILE)

# Avvia thread scraping
if __name__ == "__main__":
    t = threading.Thread(target=run_scraper)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=10000)
