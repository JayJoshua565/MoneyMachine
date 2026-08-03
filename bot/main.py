"""
Looks up one or more Pokemon cards on Cardmarket and writes their price
data to data/deals.json.

Usage:
    python main.py "Charizard ex"      # look up a single card by name
    python main.py                     # refresh every card in tracked_cards.json
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from pokemon_tcg_client import PokemonTcgClient

ROOT = Path(__file__).resolve().parent.parent
DEALS_FILE = ROOT / "data" / "deals.json"
TRACKED_FILE = ROOT / "data" / "tracked_cards.json"


def load_json(path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def lookup_card(client, name):
    """Search for a card name, pull out its Cardmarket pricing block."""
    matches, match_type = client.find_cards(name)
    results = []

    for card in matches:
        cm = card.get("cardmarket") or {}
        prices = cm.get("prices", {})

        results.append({
            "id": card.get("id"),
            "name": card.get("name"),
            "expansion": (card.get("set") or {}).get("name"),
            "number": card.get("number"),
            "rarity": card.get("rarity"),
            "image": (card.get("images") or {}).get("small"),
            "url": cm.get("url"),
            "cardmarket_updated_at": cm.get("updatedAt"),
            "price_sell_avg": prices.get("averageSellPrice"),
            "price_low": prices.get("lowPrice"),
            "price_low_ex_plus": prices.get("lowPriceExPlus"),
            "price_trend": prices.get("trendPrice"),
            "price_avg_30d": prices.get("avg30"),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        })

    return {
        "match_type": match_type,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }


def main():
    client = PokemonTcgClient()
    deals = load_json(DEALS_FILE, {})

    if len(sys.argv) > 1:
        # Ad-hoc single-card lookup (e.g. triggered by the "check now" button)
        card_names = [" ".join(sys.argv[1:])]
    else:
        # Scheduled refresh of every card you're tracking
        tracked = load_json(TRACKED_FILE, [])
        card_names = [c["name"] for c in tracked]

    for name in card_names:
        print(f"Looking up: {name}")
        try:
            deals[name] = lookup_card(client, name)
        except Exception as e:
            print(f"  failed: {e}")

    save_json(DEALS_FILE, deals)
    print(f"Saved results for {len(card_names)} card(s) to {DEALS_FILE}")


if __name__ == "__main__":
    main()
