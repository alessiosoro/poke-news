import requests
from bs4 import BeautifulSoup
import time
from flask import Flask, render_template_string

SCRAPER_API_KEY = "7781150a6c6b284bc07d9be4ea2c797b"

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Ultime notizie carte Pokémon</title>
</head>
<body>
    <h1>Ultime notizie carte Pokémon</h1>
    {% if news %}
        <ul>
        {% for item in news %}
            <li><a href="{{ item.link }}" target="_blank">{{ item.title }}</a> - {{ item.source }}</li>
        {% endfor %}
        </ul>
    {% else %}
        <p>⚠️ Nessuna notizia trovata al momento.</p>
    {% endif %}
</body>
</html>
"""

news_cache = []

def scrape_pokeguardian():
    print("🔍 Scraping PokeGuardian...")
    url = f"https://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url=https://www.pokeguardian.com/articles/news-archive"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("h2.article-title a")[:3]

    news = []
    for article in articles:
        title = article.get_text(strip=True)
        link = "https://www.pokeguardian.com" + article.get("href")
        news.append({"title": title, "link": link, "source": "PokeGuardian"})
    return news

@app.route("/")
def index():
    global news_cache
    if not news_cache:
        print("🆕 Nessuna cache trovata, avvio scraping iniziale.")
        news_cache = scrape_pokeguardian()
    return render_template_string(TEMPLATE, news=news_cache)

def update_news_loop():
    global news_cache
    while True:
        print("🔄 Aggiornamento news...")
        new_news = scrape_pokeguardian()
        if new_news != news_cache:
            print("📢 Novità rilevate, aggiornamento in corso.")
            news_cache = new_news
        else:
            print("⏸ Nessun aggiornamento trovato.")
        time.sleep(60)

if __name__ == "__main__":
    import threading
    threading.Thread(target=update_news_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
