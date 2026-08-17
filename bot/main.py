"""
Looks up one or more Pokemon cards on Cardmarket and writes their price
data to data/deals.json.

Usage:
    python main.py "Charizard ex"      # look up a single card by name
    python main.py                     # refresh every card in tracked_cards.json
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pokemon_tcg_client import PokemonTcgClient
from vinted_client import VintedClient

ROOT = Path(__file__).resolve().parent.parent
DEALS_FILE = ROOT / "data" / "deals.json"
TRACKED_FILE = ROOT / "data" / "tracked_cards.json"


def load_json(path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return default  # file exists but is empty -- treat as missing
            return json.loads(content)
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def lookup_cardmarket(client, name):
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
        })

    return match_type, results


def lookup_card(cm_client, vinted_client, name, platform, existing=None):
    """Look up a card on Cardmarket and/or Vinted, depending on `platform`
    ("both", "cardmarket", or "vinted"). If a source is skipped, its
    previously-saved data (if any) is preserved rather than wiped."""
    existing = existing or {}
    if isinstance(existing, list):
        existing = {"match_type": "exact", "cardmarket": existing, "vinted": None}

    match_type = existing.get("match_type", "none")
    cardmarket_results = existing.get("cardmarket", existing.get("results", []))
    vinted_result = existing.get("vinted")

    if platform in ("both", "cardmarket"):
        match_type, cardmarket_results = lookup_cardmarket(cm_client, name)

    if platform in ("both", "vinted"):
        vinted_result = vinted_client.search(name)

    return {
        "match_type": match_type,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "cardmarket": cardmarket_results,
        "vinted": vinted_result,
    }


def main():
    cm_client = PokemonTcgClient()
    vinted_client = VintedClient(domain=os.environ.get("VINTED_DOMAIN", "nl"))
    deals = load_json(DEALS_FILE, {})
    platform = os.environ.get("CHECK_PLATFORM", "both")
    if platform not in ("both", "cardmarket", "vinted"):
        platform = "both"

    if len(sys.argv) > 1:
        # Ad-hoc single-card lookup (e.g. triggered by the "check now" button)
        card_names = [" ".join(sys.argv[1:])]
    else:
        # Scheduled refresh of every card you're tracking
        tracked = load_json(TRACKED_FILE, [])
        card_names = [c["name"] for c in tracked]

    print(f"Platform: {platform}")

    for name in card_names:
        print(f"Looking up: {name}")
        try:
            deals[name] = lookup_card(cm_client, vinted_client, name, platform, deals.get(name))
            print(f"  Cardmarket: {len(deals[name]['cardmarket'])} printing(s)")
            vinted = deals[name]["vinted"]
            if vinted is None:
                print("  Vinted: not checked (no prior data, platform set to cardmarket-only)")
            else:
                vinted_msg = f"ok, {len(vinted['items'])} listing(s)" if vinted["ok"] else "blocked/unavailable this run"
                filtered = vinted.get("filtered_non_english", 0)
                if vinted["ok"] and filtered:
                    vinted_msg += f" ({filtered} non-English filtered out)"
                print(f"  Vinted: {vinted_msg}")
        except Exception as e:
            print(f"  failed: {e}")

    save_json(DEALS_FILE, deals)
    print(f"Saved results for {len(card_names)} card(s) to {DEALS_FILE}")


if __name__ == "__main__":
    main()
