"""
Client for the pokemontcg.io API (docs: https://docs.pokemontcg.io).

Why this instead of calling Cardmarket directly: Cardmarket has paused
accepting new applications for their own API. pokemontcg.io is a free,
long-running community API whose card objects already include a
"cardmarket" pricing block (averageSellPrice, lowPrice, trendPrice, ...)
sourced from Cardmarket itself. Free API key strongly recommended for
higher rate limits: sign up at https://dev.pokemontcg.io/
"""

import os
import requests

BASE_URL = "https://api.pokemontcg.io/v2"


class PokemonTcgClient:
    def __init__(self, api_key=None):
        # Works without a key (lower rate limit) or with one (much higher).
        self.api_key = api_key or os.environ.get("POKEMONTCG_API_KEY")

    def _get(self, path, params=None):
        headers = {"X-Api-Key": self.api_key} if self.api_key else {}
        response = requests.get(
            f"{BASE_URL}/{path}", params=params or {}, headers=headers, timeout=20
        )
        response.raise_for_status()
        return response.json()

    def find_cards(self, name):
        """
        Search for cards by name. Tries an exact phrase match first (best
        for official names like "Charizard ex"). If that finds nothing,
        falls back to matching any individual word in the name -- this
        catches nickname-style or partial searches (e.g. "Corocoro Mewtwo"
        falls back to matching every card with "Mewtwo" in the name, since
        "Corocoro" is a set/promo nickname, not part of the card's name).

        Returns (cards, match_type) where match_type is "exact", "broad",
        or "none".
        """
        data = self._get("cards", params={"q": f'name:"{name}"'})
        cards = data.get("data", [])
        if cards:
            return cards, "exact"

        words = [w for w in name.split() if w]
        if len(words) > 1:
            query = " OR ".join(f'name:"{w}"' for w in words)
            data = self._get("cards", params={"q": query})
            cards = data.get("data", [])
            if cards:
                return cards, "broad"

        return [], "none"
