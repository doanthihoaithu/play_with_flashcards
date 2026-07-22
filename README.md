# English Flashcards

A Streamlit flashcard app for studying English vocabulary, with the Vietnamese
text on the front and the English translation on the back. Works on both
desktop and mobile.

## Run

```bash
pip install -r requirements.txt
cp conf/config.example.yaml conf/config.yaml  # optional, for local overrides
streamlit run src/app.py
```

## Adding decks

Drop a new `*.yaml` file into `decks/`:

```yaml
name: "My Deck"
cards:
  - key_infor: "noun"
    vietnamese_text: "quả táo"
    english_text: "apple"
```

- `key_infor` — a short tag shown on the card (e.g. part of speech, topic).
- `vietnamese_text` — shown on the front.
- `english_text` — shown on the back.

Tap/click a card to flip it. Use the sidebar to pick a deck and toggle
shuffling.