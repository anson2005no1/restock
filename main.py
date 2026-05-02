import time
import random
import requests
from bs4 import BeautifulSoup

URL = "https://cortisofficial.us/"
WEBHOOK_URL = "https://discord.com/api/webhooks/1499837939956322525/JYfllYd09e6qopnwFQ9j1ItprRuN7vZYZe3W0WwrNtflNcNdFiDNWfOCfr_WMoHCMy7E"

headers = {
    "User-Agent": "Mozilla/5.0"
}

COOLDOWN_STATUS_CODES = {503, 429, 403}


def send_discord(message: str):
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload, timeout=10)


def check_products():
    res = requests.get(URL, headers=headers, timeout=10)

    if res.status_code in COOLDOWN_STATUS_CODES:
        raise RuntimeError(f"Hit status code {res.status_code}")

    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    products = soup.select("li.grid-item__wrapper")[:3]

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

    message = "\n\n".join(lines + ["------------------------------"])
    send_discord(message)


while True:
    try:
        check_products()

        # 正常情況：休息 60～180 秒
        sleep_seconds = random.randint(60, 180)
        print(f"Checked successfully. Sleeping {sleep_seconds} seconds.")
        time.sleep(sleep_seconds)

    except RuntimeError as e:
        # 遇到 503 / 429 / 403：休息 15～20 分鐘
        sleep_seconds = random.randint(15 * 60, 20 * 60)
        print(f"{e}. Cooling down for {sleep_seconds // 60} minutes.")
        send_discord("被封鎖了啦...要等15-20分鐘再繼續試試")
        time.sleep(sleep_seconds)

    except requests.RequestException as e:
        # 其他網路錯誤：避免程式直接死掉，先短暫休息
        sleep_seconds = random.randint(60, 180)
        print(f"Request error: {e}. Sleeping {sleep_seconds} seconds.")
        time.sleep(sleep_seconds)

    except Exception as e:
        # 其他未知錯誤：避免直接中斷
        sleep_seconds = random.randint(60, 180)
        print(f"Unexpected error: {e}. Sleeping {sleep_seconds} seconds.")
        time.sleep(sleep_seconds)
