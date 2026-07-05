"""
Bot de búsqueda de vehículos en Mercado Libre (Argentina).

Busca Chevrolet Onix, transmisión automática, entre 10.000 y 55.000 km,
año 2020 en adelante. Notifica por Telegram las publicaciones nuevas
que todavía no había visto (guarda un historial en seen_ids.json).

Pensado para correr periódicamente vía GitHub Actions, pero también
se puede correr a mano con: python ml_bot.py
"""

import json
import os
import sys
import time
from pathlib import Path

import requests

# ------------------------------------------------------------------
# CONFIGURACIÓN DE LA BÚSQUEDA — ajustá estos valores a gusto
# ------------------------------------------------------------------
SITE_ID = "MLA"                     # Argentina
CATEGORY_ID = "MLA1744"             # Autos y Camionetas
QUERY = "Chevrolet Onix"            # texto de búsqueda

YEAR_MIN = 2020                     # año mínimo (inclusive)
KM_MIN = 10000                      # km mínimo
KM_MAX = 55000                      # km máximo
TRANSMISSION_KEYWORDS = ["automátic", "automatic"]  # case-insensitive, sin acentos raros

PAGE_SIZE = 50
MAX_PAGES = 4                       # tope de paginación por corrida (seguridad)

# ------------------------------------------------------------------
# CONFIGURACIÓN DE TELEGRAM (se leen de variables de entorno / secrets)
# ------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

SEEN_IDS_FILE = Path(__file__).parent / "seen_ids.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ML-Onix-Bot/1.0)"}


def load_seen_ids() -> set:
    if SEEN_IDS_FILE.exists():
        try:
            return set(json.loads(SEEN_IDS_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def save_seen_ids(ids: set) -> None:
    SEEN_IDS_FILE.write_text(
        json.dumps(sorted(ids), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def search_listings() -> list:
    """Devuelve la lista cruda de resultados de búsqueda (varias páginas)."""
    results = []
    for page in range(MAX_PAGES):
        offset = page * PAGE_SIZE
        url = f"https://api.mercadolibre.com/sites/{SITE_ID}/search"
        params = {
            "category": CATEGORY_ID,
            "q": QUERY,
            "limit": PAGE_SIZE,
            "offset": offset,
        }
        resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            print(f"[WARN] búsqueda devolvió {resp.status_code}: {resp.text[:300]}")
            break
        data = resp.json()
        items = data.get("results", [])
        if not items:
            break
        results.extend(items)
        total = data.get("paging", {}).get("total", 0)
        if offset + PAGE_SIZE >= total:
            break
        time.sleep(0.5)  # buen ciudadano con la API
    return results


def get_item_detail(item_id: str) -> dict | None:
    url = f"https://api.mercadolibre.com/items/{item_id}"
    resp = requests.get(url, headers=HEADERS, timeout=20)
    if resp.status_code != 200:
        return None
    return resp.json()


def extract_attribute(attributes: list, keyword: str) -> str | None:
    """Busca un atributo por nombre (contiene keyword, case-insensitive) y
    devuelve su value_name."""
    keyword = keyword.lower()
    for attr in attributes or []:
        name = (attr.get("name") or "").lower()
        if keyword in name:
            return attr.get("value_name")
    return None


def matches_filters(detail: dict) -> bool:
    attributes = detail.get("attributes", [])

    # Año
    year_str = extract_attribute(attributes, "año")
    try:
        year = int(year_str) if year_str else None
    except ValueError:
        year = None
    if year is None or year < YEAR_MIN:
        return False

    # Kilómetros
    km_str = extract_attribute(attributes, "kilóm") or extract_attribute(attributes, "kilom")
    try:
        km = int(str(km_str).replace(".", "").replace(",", "")) if km_str else None
    except ValueError:
        km = None
    if km is None or not (KM_MIN <= km <= KM_MAX):
        return False

    # Transmisión
    trans_str = (
        extract_attribute(attributes, "transmisi")
        or extract_attribute(attributes, "caja")
        or ""
    )
    trans_str = trans_str.lower()
    if not any(kw in trans_str for kw in TRANSMISSION_KEYWORDS):
        return False

    return True


def notify_telegram(item: dict, detail: dict) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[INFO] (sin Telegram configurado) Nuevo match: {item.get('permalink')}")
        return

    title = item.get("title", "Vehículo")
    price = item.get("price")
    currency = item.get("currency_id", "")
    link = item.get("permalink", "")
    attrs = detail.get("attributes", [])
    year = extract_attribute(attrs, "año") or "?"
    km = extract_attribute(attrs, "kilóm") or extract_attribute(attrs, "kilom") or "?"

    text = (
        f"🚗 *{title}*\n"
        f"Año: {year} | Km: {km}\n"
        f"Precio: {currency} {price:,.0f}\n".replace(",", ".")
        + f"{link}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    resp = requests.post(url, json=payload, timeout=20)
    if resp.status_code != 200:
        print(f"[WARN] error enviando a Telegram: {resp.status_code} {resp.text[:300]}")


def main() -> int:
    seen_ids = load_seen_ids()
    listings = search_listings()
    print(f"[INFO] {len(listings)} resultados crudos de la búsqueda.")

    new_matches = 0
    for item in listings:
        item_id = item.get("id")
        if not item_id or item_id in seen_ids:
            continue

        detail = get_item_detail(item_id)
        seen_ids.add(item_id)  # lo marcamos como visto igual, matchee o no
        if not detail:
            continue

        if matches_filters(detail):
            new_matches += 1
            notify_telegram(item, detail)
        time.sleep(0.3)

    save_seen_ids(seen_ids)
    print(f"[INFO] {new_matches} publicaciones nuevas que cumplen los filtros.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
