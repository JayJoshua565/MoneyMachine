# Pokemon Card Deal Tracker

Looks up a Pokemon card's price on Cardmarket (official API) and saves the
results so you can browse them via a simple search interface.

## Setup

**Note:** Cardmarket has paused accepting new applications for their own
API, so this bot gets Cardmarket's pricing data via
[pokemontcg.io](https://pokemontcg.io) instead — a free, long-running
community API whose card data already includes a Cardmarket pricing block
(average sell price, low price, trend price) sourced from Cardmarket itself.

### 1. Get a free pokemontcg.io API key (optional but recommended)
1. Go to https://dev.pokemontcg.io/ and sign up (free).
2. Copy your API key. Without one you get 1,000 requests/day; with one, 20,000/day.

### 2. Add it as a GitHub Secret
In your repo: **Settings -> Secrets and variables -> Actions -> New repository secret**,
add:
- `POKEMONTCG_API_KEY`

Never commit this value into any file in the repo.

### 3. Try it locally first (optional but recommended)
```bash
cd bot
pip install -r requirements.txt
export POKEMONTCG_API_KEY=xxx
python main.py "Charizard ex"
cat ../data/deals.json
```

### 4. Let GitHub Actions run it
- `.github/workflows/check-deals.yml` runs automatically every 2 hours for
  every card listed in `data/tracked_cards.json`.
- You can also trigger it manually any time: go to the **Actions** tab ->
  "Check card prices" -> **Run workflow** -> optionally type a card name to
  check just that one card right now.

## Data files
- `data/tracked_cards.json` — cards refreshed automatically on schedule. Add more by editing this list.
- `data/deals.json` — the bot's latest results per card (this is what a future frontend will read from).

## Vinted listings (best-effort, unofficial)

The bot also searches Vinted's internal search endpoint for listings
matching your card name. Read this before relying on it:

- Vinted has **no official public API** for this. We call the same
  endpoint their own website uses, with a normal browser User-Agent
  and nothing more -- no proxies, no fingerprint spoofing, no bot-detection
  bypass tooling.
- Vinted actively runs bot detection (Datadome) on this endpoint, so this
  **will sometimes get blocked** and return no results. That's expected,
  not a bug -- the site checks for that (`vinted.ok === false`) and shows
  a "couldn't reach Vinted this time" message with a direct link to
  search Vinted yourself instead.
- Results are a **plain text match**, not tied to a specific card printing
  the way Cardmarket's catalog is. Always eyeball the listing photo/title
  before trusting it's the exact card you're after.
- Defaults to `vinted.nl`. Change the domain via the `VINTED_DOMAIN`
  environment variable (e.g. `fr`, `de`, `co.uk`) if you shop a different
  Vinted marketplace.

## Favorites

Tap the star on any Cardmarket card or Vinted listing to save it to the
Favorites tab. As shipped, favorites reset if you reload the page — that's
intentional for compatibility with preview environments. To make them
persist on your real deployed site, replace this line in `index.html`:

```js
let favorites = { cardmarket: {}, vinted: {} };
```

with:

```js
let favorites = JSON.parse(localStorage.getItem('favorites') || '{"cardmarket":{},"vinted":{}}');
```

and add this line inside `updateFavCount()`, right after the count is
updated:

```js
localStorage.setItem('favorites', JSON.stringify(favorites));
```

## What's next
Once this is fetching real data reliably, the next step is a small
GitHub Pages search page that reads `data/deals.json` (instant, free) plus
a "check now" button that triggers the workflow above on demand.
Vinted comparison is a planned phase 2 — see project notes.
