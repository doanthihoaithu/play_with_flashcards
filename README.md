# English Flashcards

A Streamlit flashcard app for studying English vocabulary, with the Vietnamese
text on the front and the English translation on the back. Works on both
desktop and mobile.

The app has three pages, listed in the sidebar navigation menu:

- **Introduction** — a short welcome/overview.
- **Flashcards** — the deck picker, filters, and flip cards described below.
- **Shadowing** — coming soon.

## Run

```bash
pip install -r requirements.txt
cp conf/config.example.yaml conf/config.yaml  # optional, for local overrides
streamlit run src/app.py
```

## Adding decks

Drop a new `*.csv` file into `decks/`. The deck name is taken from the file
name (e.g. `daily_verbs.csv` becomes "Daily Verbs"), and each row is one card:

```csv
key_infor,vietnamese_text,english_text
noun,quả táo,apple
```

- `key_infor` — a short tag shown on the card (e.g. part of speech, topic).
- `vietnamese_text` — shown on the front. (`vietnamese_meaning` also accepted.)
- `english_text` — shown on the back. (`english_meaning` also accepted.)

Other columns (e.g. `card_id`) are ignored, and rows missing the Vietnamese
or English value are skipped.

Tap/click a card to flip it. Use the sidebar to pick a deck and toggle
shuffling.