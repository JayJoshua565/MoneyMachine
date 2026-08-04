"""
Lightweight client for Vinted's search results.

IMPORTANT -- read this before relying on it:
Vinted has no official public API for this kind of search. This calls
the same internal endpoint their own website uses (api/v2/catalog/items),
with a normal browser-style User-Agent and nothing more: no TLS
fingerprint spoofing, no residential proxies, no CAPTCHA/Datadome bypass
tooling. Vinted actively runs Datadome bot-detection on this endpoint,
so this WILL sometimes -- possibly often -- get blocked or rate limited.
That's an accepted tradeoff for a personal project using an unofficial
integration. If it stops working, that's expected, not a bug to "fix"
by adding evasion techniques.

Vinted listings are free-text and not tied to a specific card printing
the way Cardmarket's catalog is, so results here are a best-effort text
match, not guaranteed to all be the exact card you searched for -- you
still need to eyeball titles/photos before trusting a "deal".
"""

import re
import requests

# Best-effort text markers for non-English print versions. Sellers use these
# inconsistently (or not at all), so this is a heuristic, not a verified
# data field -- it'll catch clearly-tagged foreign listings but can miss
# untagged ones, and could rarely mis-flag an English listing that happens
# to mention a foreign word (e.g. describing a Japanese-style illustration).
NON_ENGLISH_MARKERS = [
    r'\bjap\w*\b', r'\bjp\b', r'\bnihongo\b',
    r'\bfr\b', r'\bfran[çc]ais\w*\b', r'\bvf\b',
    r'\bde\b', r'\bdeutsch\w*\b', r'\ballemand\w*\b',
    r'\bit\b', r'\bitalien\w*\b', r'\bitaliano\b',
    r'\bes\b', r'\bespa[ñn]ol\w*\b', r'\bespagnol\w*\b',
    r'\bkr\b', r'\bkorean\w*\b', r'\bcorean\w*\b',
    r'\bchinese\b', r'\bchinois\w*\b',
    r'\bpt\b', r'\bportugu[eê]s\w*\b',
    r'\bpl\b', r'\bpolish\w*\b', r'\bpolonais\w*\b',
]
_NON_ENGLISH_RE = re.compile('|'.join(NON_ENGLISH_MARKERS), re.IGNORECASE)


def _looks_english(title):
    if not title:
        return True  # no title text to judge by -- don't exclude on a guess
    return not _NON_ENGLISH_RE.search(title)


class VintedClient:
    def __init__(self, domain="nl", per_page=20):
        self.domain = domain
        self.per_page = per_page
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
        })
        self._warmed_up = False

    def _warm_up(self):
        # A normal browser loads the homepage before calling the API,
        # which sets session cookies. We do the same, once per run.
        if not self._warmed_up:
            try:
                self.session.get(f"https://www.vinted.{self.domain}/", timeout=15)
            except requests.RequestException:
                pass
            self._warmed_up = True

    def search(self, query, english_only=True):
        """
        Returns {"ok": bool, "status_code": int|None, "items": [...],
        "filtered_non_english": int}. Never raises -- failures are reported
        in the returned dict so a blocked Vinted check doesn't take down
        the whole bot run.
        """
        self._warm_up()
        try:
            response = self.session.get(
                f"https://www.vinted.{self.domain}/api/v2/catalog/items",
                params={
                    "search_text": query,
                    "per_page": self.per_page,
                    "order": "relevance",
                },
                timeout=15,
            )
            if response.status_code != 200:
                return {"ok": False, "status_code": response.status_code, "items": [], "filtered_non_english": 0}

            data = response.json()
            items = [
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "price": (item.get("price") or {}).get("amount"),
                    "currency": (item.get("price") or {}).get("currency_code"),
                    "url": item.get("url"),
                    "photo": (item.get("photo") or {}).get("url"),
                    "brand": item.get("brand_title"),
                    "seller": (item.get("user") or {}).get("login"),
                }
                for item in data.get("items", [])
            ]

            filtered_count = 0
            if english_only:
                before = len(items)
                items = [i for i in items if _looks_english(i["title"])]
                filtered_count = before - len(items)

            return {"ok": True, "status_code": 200, "items": items, "filtered_non_english": filtered_count}

        except requests.RequestException as e:
            return {"ok": False, "status_code": None, "error": str(e), "items": [], "filtered_non_english": 0}
        except ValueError:
            # Response wasn't valid JSON -- usually means we hit a
            # Datadome challenge page instead of the real API.
            return {"ok": False, "status_code": response.status_code, "items": [], "filtered_non_english": 0, "error": "non-JSON response (likely bot-blocked)"}
