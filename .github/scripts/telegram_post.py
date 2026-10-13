"""Blog maqolasini Telegram kanalga rasm, tavsif va "O'qish" tugmasi bilan joylaydi.

Ma'lumotlar maqola sahifasining meta-teglaridan olinadi (og:title, og:description,
og:image, canonical), shuning uchun yangi maqola uchun hech narsa qo'shimcha yozish shart emas.
"""
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
FILES = os.environ.get("FILES", "").split()


def meta(page: str, attr: str, name: str) -> str:
    m = re.search(rf'<meta\s+{attr}="{re.escape(name)}"\s+content="([^"]*)"', page)
    return html.unescape(m.group(1)) if m else ""


def wait_until_live(url: str, timeout: int = 600) -> None:
    """GitHub Pages yangi sahifani chiqarguncha kutadi (odatda 1–2 daqiqa)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                if r.status == 200:
                    return
        except urllib.error.URLError:
            pass
        print(f"  {url} hali ochilmadi, 15 soniya kutamiz…")
        time.sleep(15)
    sys.exit(f"Sahifa {timeout} soniyada ochilmadi: {url}")


def send(path: str) -> None:
    page = open(path, encoding="utf-8").read()
    title = meta(page, "property", "og:title")
    desc = meta(page, "property", "og:description") or meta(page, "name", "description")
    image = meta(page, "property", "og:image")
    m = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', page)
    url = m.group(1) if m else ""
    if not (title and image and url):
        sys.exit(f"{path}: og:title, og:image yoki canonical topilmadi")

    print(f"Maqola: {title}\n  {url}")
    wait_until_live(url)
    wait_until_live(image)

    caption = f"<b>{html.escape(title)}</b>\n\n{html.escape(desc)}\n\n#blog"
    payload = {
        "chat_id": CHAT_ID,
        "photo": image,
        "caption": caption,
        "parse_mode": "HTML",
        "reply_markup": json.dumps({"inline_keyboard": [[{"text": "Maqolani oʻqish →", "url": url}]]}),
    }
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
        data=urllib.parse.urlencode(payload).encode(),
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.load(r)
    except urllib.error.HTTPError as e:
        # Tokenni logga chiqarmaslik uchun faqat Telegram javobini ko'rsatamiz
        sys.exit(f"Telegram xatosi {e.code}: {e.read().decode(errors='replace')}")
    if not result.get("ok"):
        sys.exit(f"Telegram xatosi: {result}")
    print("  ✅ Kanalga joylandi")


def main() -> None:
    if not TOKEN:
        sys.exit("TELEGRAM_BOT_TOKEN secret qo'shilmagan")
    if not CHAT_ID:
        sys.exit("TELEGRAM_CHAT_ID variable qo'shilmagan")
    for path in FILES:
        if os.path.exists(path):
            send(path)
        else:
            print(f"{path} topilmadi, o'tkazib yuborildi")


if __name__ == "__main__":
    main()
