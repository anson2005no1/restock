import time
import random
import requests
from bs4 import BeautifulSoup

URL = "https://cortisofficial.us/"
WEBHOOK_URL = "https://discord.com/api/webhooks/1499837939956322525/JYfllYd09e6qopnwFQ9j1ItprRuN7vZYZe3W0WwrNtflNcNdFiDNWfOCfr_WMoHCMy7E"
BOT_NAME = "幫忙檢查有沒有貨的勞工"
BOT_AVATAR = "https://raw.githubusercontent.com/anson2005no1/restock/refs/heads/main/1.jpg"
COOLDOWN_STATUS_CODES = {503, 429, 403}

headers = {
    "User-Agent": "Mozilla/5.0"
}

last_tags = {}
first_run = True

def send_discord(title, tags, price, product_url, image_url=None, status=None):
    if status == "error":
        embed_title = "⚠️ 系統通知"
        color = 0xFFA500
    else:
        is_sold_out = any("Sold out" in tag for tag in tags)
        embed_title = f"{'❌' if is_sold_out else '✅'} {'售完通知' if is_sold_out else '有貨通知'}"
        color = 0xFF0000 if is_sold_out else 0x00FF00

    embed = {
        "title": embed_title,
        "description": (
            f"**{title}**\n"
            f"Tags: {', '.join(tags) if tags else 'No tags'}\n"
            f"Price: {price}\n\n"
            f"{product_url}"
        ),
        "color": color,
    }

    if image_url:
        embed["thumbnail"] = {"url": image_url}

    payload = {
        "embeds": [embed],
        "username": BOT_NAME,
        "avatar_url": BOT_AVATAR if BOT_AVATAR else None
    }
    requests.post(WEBHOOK_URL, json=payload, timeout=10)

def fix_url(src):
    if not src:
        return None
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("/"):
        return URL.rstrip("/") + src
    return src

def check_products():
    global first_run, last_tags

    res = requests.get(URL, headers=headers, timeout=10)

    if res.status_code in COOLDOWN_STATUS_CODES:
        raise RuntimeError(f"Hit status code {res.status_code}")

    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    products = soup.select("li.grid-item__wrapper")[:3]

    current_products = []
    has_tag_update = False

    for product in products:
        title_tag = product.select_one("p.text_heading_md")
        title = title_tag.get_text(strip=True) if title_tag else "No title"

        tags = [
            tag.get_text(strip=True)
            for tag in product.select(".card__tags .card__single-tag")
        ]

        price_tag = product.select_one(".price__current")
        price = price_tag.get_text(strip=True) if price_tag else "No price"

        img_tag = product.select_one("img")
        image_url = fix_url(img_tag.get("src")) if img_tag else None

        link_tag = product.select_one('a[href^="/products/"]')
        product_url = fix_url(link_tag.get("href")) if link_tag else URL

        current_products.append({
            "title": title,
            "tags": tags,
            "price": price,
            "product_url": product_url,
            "image_url": image_url,
        })

        key = product_url

        # 第一次看到這個商品，只記錄，不通知
        if key not in last_tags:
            last_tags[key] = tags
            continue

        # 比對 tags
        if tags != last_tags[key]:
            has_tag_update = True
            last_tags[key] = tags

    if first_run:
        first_run = False
        print("First run: saved initial tags, no Discord message sent.")
        return

    # 只要任一商品的 tags 改變，就傳送這三個商品
    if has_tag_update:
        for info in current_products:
            send_discord(
                info["title"],
                info["tags"],
                info["price"],
                info["product_url"],
                info["image_url"]
            )

        requests.post(
            WEBHOOK_URL,
            json={
                "content": "----------------------------------------",
                "username": BOT_NAME,
                "avatar_url": BOT_AVATAR if BOT_AVATAR else None
            },
            timeout=10
        )

        print("Tags changed. Sent Discord notification.")
    else:
        print("Tags unchanged. No Discord message sent.")

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
        send_discord(
            "被封了啦...要等15-20分鐘再繼續試試！",
            [],
            "N/A",
            URL,
            status="error"
        )
        time.sleep(sleep_seconds)

    except requests.RequestException as e:
        # 其他網路錯誤：避免程式直接死掉，先短暫休息
        sleep_seconds = random.randint(60, 180)
        print(f"Request error: {e}. Sleeping {sleep_seconds} seconds.")
        send_discord(
            "網路錯誤...會先暫停 1-3 分鐘！",
            [],
            "N/A",
            URL,
            status="error"
        )
        time.sleep(sleep_seconds)

    except Exception as e:
        # 其他未知錯誤：避免直接中斷
        sleep_seconds = random.randint(60, 180)
        print(f"Unexpected error: {e}. Sleeping {sleep_seconds} seconds.")
        send_discord(
            "未知錯誤...先暫停一下！等等會自己重試...",
            [],
            "N/A",
            URL,
            status="error"
        )
        time.sleep(sleep_seconds)
