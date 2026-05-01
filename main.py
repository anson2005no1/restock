import time
import requests
from bs4 import BeautifulSoup

URL = "https://cortisofficial.us/"
WEBHOOK_URL = "https://discord.com/api/webhooks/1499837939956322525/JYfllYd09e6qopnwFQ9j1ItprRuN7vZYZe3W0WwrNtflNcNdFiDNWfOCfr_WMoHCMy7E"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def send_discord(message: str):
    """傳送訊息到 Discord"""
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload)

def check_products():
    res = requests.get(URL, headers=headers, timeout=10)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    products = soup.select("li.grid-item__wrapper")[:8]

    lines = []
    for i, product in enumerate(products, start=1):
        title_tag = product.select_one("p.text_heading_md")
        title = title_tag.get_text(strip=True) if title_tag else "No title"

        tags = [
            tag.get_text(strip=True)
            for tag in product.select(".card__tags .card__single-tag")
        ]

        price_tag = product.select_one(".price__current")
        price = price_tag.get_text(strip=True) if price_tag else "No price"

        lines.append(
            f"**{i}. {title}**\n"
            f"　Tags: {', '.join(tags) if tags else 'No tags'}\n"
            f"　Price: {price}"
        )

    message = "\n\n".join(lines)
    send_discord(message)

while True:
    check_products()
    time.sleep(60)
