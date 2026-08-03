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

## What's next
Once this is fetching real data reliably, the next step is a small
GitHub Pages search page that reads `data/deals.json` (instant, free) plus
a "check now" button that triggers the workflow above on demand.
Vinted comparison is a planned phase 2 — see project notes.
