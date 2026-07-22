import html
import random
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
import yaml

from deck_loader import Card, load_decks

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONF_DIR = PROJECT_ROOT / "conf"


def load_config() -> dict:
    config: dict = {}
    example_path = CONF_DIR / "config.example.yaml"
    if example_path.exists():
        config.update(yaml.safe_load(example_path.read_text(encoding="utf-8")) or {})
    local_path = CONF_DIR / "config.yaml"
    if local_path.exists():
        config.update(yaml.safe_load(local_path.read_text(encoding="utf-8")) or {})
    return config


def new_order(n_cards: int, shuffle: bool) -> list:
    order = list(range(n_cards))
    if shuffle:
        random.shuffle(order)
    return order


def render_card(card: Card) -> None:
    front = html.escape(card.vietnamese_text)
    back = html.escape(card.english_text)
    tag = html.escape(card.key_infor)

    card_html = f"""
    <style>
      * {{ box-sizing: border-box; }}
      .flip-card {{
        width: 100%;
        max-width: 480px;
        height: 260px;
        margin: 0 auto;
        perspective: 1200px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        cursor: pointer;
      }}
      .flip-card-inner {{
        position: relative;
        width: 100%;
        height: 100%;
        text-align: center;
        transition: transform 0.5s;
        transform-style: preserve-3d;
      }}
      .flip-card.flipped .flip-card-inner {{
        transform: rotateY(180deg);
      }}
      .flip-card-front, .flip-card-back {{
        position: absolute;
        inset: 0;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
        border-radius: 18px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
      }}
      .flip-card-front {{
        background: linear-gradient(135deg, #4facfe 0%, #00c6ff 100%);
        color: #ffffff;
      }}
      .flip-card-back {{
        background: linear-gradient(135deg, #43e97b 0%, #38d9a9 100%);
        color: #063d2b;
        transform: rotateY(180deg);
      }}
      .badge {{
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        background: rgba(255, 255, 255, 0.35);
        padding: 4px 12px;
        border-radius: 999px;
        margin-bottom: 14px;
      }}
      .main-text {{
        font-size: clamp(1.3rem, 6vw, 2.2rem);
        font-weight: 700;
        word-break: break-word;
        line-height: 1.3;
      }}
      .hint {{
        margin-top: 14px;
        font-size: 0.8rem;
        opacity: 0.85;
      }}
    </style>
    <div class="flip-card" onclick="this.classList.toggle('flipped')">
      <div class="flip-card-inner">
        <div class="flip-card-front">
          <div class="badge">{tag}</div>
          <div class="main-text">{front}</div>
          <div class="hint">Tap card to see English</div>
        </div>
        <div class="flip-card-back">
          <div class="badge">{tag}</div>
          <div class="main-text">{back}</div>
          <div class="hint">Tap card to see Vietnamese</div>
        </div>
      </div>
    </div>
    """
    components.html(card_html, height=300, scrolling=False)


def main() -> None:
    config = load_config()
    app_title = config.get("app_title", "English Flashcards")
    decks_dir = PROJECT_ROOT / config.get("decks_dir", "decks")
    default_shuffle = bool(config.get("shuffle_by_default", False))

    st.set_page_config(page_title=app_title, page_icon="\U0001F5C2️", layout="centered")
    st.title(app_title)

    decks = load_decks(decks_dir)
    if not decks:
        st.warning(
            f"No decks found in `{decks_dir}`. Add a `*.yaml` file there with a `name` "
            "and a `cards` list, each card having `key_infor`, `vietnamese_text`, "
            "and `english_text`."
        )
        st.stop()

    deck_names = [d.name for d in decks]

    with st.sidebar:
        st.header("Decks")
        selected_name = st.selectbox("Choose a deck to study", deck_names)
        shuffle_on = st.checkbox("Shuffle cards", value=default_shuffle)

    deck = next(d for d in decks if d.name == selected_name)

    # Reset session state whenever the deck or shuffle setting changes.
    state_key = (selected_name, shuffle_on)
    if st.session_state.get("state_key") != state_key:
        st.session_state.state_key = state_key
        st.session_state.order = new_order(len(deck.cards), shuffle_on)
        st.session_state.pos = 0

    order = st.session_state.order
    pos = st.session_state.pos
    total = len(order)

    st.caption(f"Card {pos + 1} of {total}")
    st.progress((pos + 1) / total)

    current_card = deck.cards[order[pos]]
    render_card(current_card)

    col_prev, col_shuffle, col_next = st.columns(3)
    with col_prev:
        if st.button("◀ Previous", use_container_width=True, disabled=(pos == 0)):
            st.session_state.pos = max(0, pos - 1)
            st.rerun()
    with col_shuffle:
        if st.button("\U0001F500 Reshuffle", use_container_width=True):
            st.session_state.order = new_order(len(deck.cards), True)
            st.session_state.pos = 0
            st.rerun()
    with col_next:
        if st.button("Next ▶", use_container_width=True, disabled=(pos == total - 1)):
            st.session_state.pos = min(total - 1, pos + 1)
            st.rerun()


if __name__ == "__main__":
    main()