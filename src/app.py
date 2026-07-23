import html
import random
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
import yaml

from deck_loader import Card, load_decks

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONF_DIR = PROJECT_ROOT / "conf"

_BOLD_MARKERS = re.compile(r"\*\*(.+?)\*\*")


def _format_highlighted(text: str) -> str:
    """Escape text for HTML, then turn **word** markers into <strong> tags."""
    escaped = html.escape(text)
    return _BOLD_MARKERS.sub(r"<strong>\1</strong>", escaped)


def _strip_bold_markers(tokens: list) -> list:
    """Pair each raw word token with whether it falls inside a **bold** span.

    A bold span's ** markers can sit on the first/last token of a
    multi-word phrase (e.g. "**National", "Baking", "Company**,"), so this
    has to track open/close state across the token sequence rather than
    matching ** pairs within a single token.
    """
    result = []
    in_bold = False
    for token in tokens:
        marker_count = token.count("**")
        clean = token.replace("**", "")
        if marker_count == 0:
            result.append((clean, in_bold))
        elif marker_count == 1:
            result.append((clean, True))
            in_bold = not in_bold
        else:  # both open and closed within this single token
            result.append((clean, True))
    return result


def _render_word_ipa_row(word_ipa_pairs: list) -> str:
    """Build the word-aligned English + IPA row: one stacked unit per word."""
    words = [w for w, _ in word_ipa_pairs]
    ipas = [i for _, i in word_ipa_pairs]
    bolded_words = _strip_bold_markers(words)

    units = []
    for (clean_word, is_bold), ipa in zip(bolded_words, ipas):
        word_html = html.escape(clean_word)
        if is_bold:
            word_html = f"<strong>{word_html}</strong>"
        ipa_html = html.escape(ipa)
        units.append(
            '<span class="word-unit">'
            f'<span class="word-unit-word">{word_html}</span>'
            f'<span class="word-unit-ipa">{ipa_html}</span>'
            "</span>"
        )
    return "".join(units)


def _card_font_size(text: str) -> str:
    """Pick a smaller font size the longer the (plain) text is."""
    length = len(_BOLD_MARKERS.sub(r"\1", text))
    if length <= 40:
        return "clamp(0.85rem, 3.2vw, 1.15rem)"
    if length <= 90:
        return "clamp(0.75rem, 2.6vw, 1rem)"
    if length <= 160:
        return "clamp(0.65rem, 2.2vw, 0.9rem)"
    return "clamp(0.55rem, 1.8vw, 0.78rem)"


def _key_infor_font_size(english_sentence: str) -> str:
    """Badge size: normal (larger) default, but once the English sentence
    is long enough to shrink its own font, shrink key_infor to match it."""
    length = len(_BOLD_MARKERS.sub(r"\1", english_sentence))
    if length <= 90:
        return "clamp(1.1rem, 4.5vw, 1.6rem)"
    return _card_font_size(english_sentence)


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
    tag = html.escape(card.key_infor)
    card_id = html.escape(card.card_id)
    front_size = _card_font_size(card.vietnamese_text)
    back_size = _card_font_size(card.english_text)
    tag_size = _key_infor_font_size(card.english_text)

    if card.word_ipa_pairs:
        back_content = (
            f'<div class="word-row" style="font-size: {back_size};">'
            f"{_render_word_ipa_row(card.word_ipa_pairs)}"
            "</div>"
        )
    else:
        back = _format_highlighted(card.english_text)
        ipa_fallback = (
            f'<div class="ipa-fallback">{html.escape(card.english_ipa)}</div>'
            if card.english_ipa
            else ""
        )
        back_content = (
            f'<div class="card-text" style="font-size: {back_size};">{back}</div>'
            f"{ipa_fallback}"
        )

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
        overflow-y: auto;
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
      .card-id {{
        position: absolute;
        top: 10px;
        left: 14px;
        font-size: 0.75rem;
        font-weight: 600;
        opacity: 0.75;
      }}
      .badge {{
        font-size: clamp(1.1rem, 4.5vw, 1.6rem);
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        background: rgba(255, 255, 255, 0.35);
        padding: 6px 16px;
        border-radius: 999px;
        margin-bottom: 14px;
      }}
      .card-text {{
        font-size: clamp(0.85rem, 3.2vw, 1.15rem);
        font-weight: 400;
        word-break: break-word;
        line-height: 1.3;
      }}
      .card-text strong {{
        font-weight: 700;
      }}
      .word-row {{
        display: flex;
        flex-wrap: wrap;
        align-items: flex-start;
        justify-content: center;
        row-gap: 10px;
        column-gap: 10px;
      }}
      .word-unit {{
        display: flex;
        flex-direction: column;
        align-items: center;
      }}
      .word-unit-word {{
        font-weight: 400;
        line-height: 1.25;
        word-break: break-word;
      }}
      .word-unit-word strong {{
        font-weight: 700;
      }}
      .word-unit-ipa {{
        margin-top: 2px;
        font-size: 0.65em;
        font-weight: 400;
        color: currentColor;
        opacity: 0.65;
        line-height: 1.2;
      }}
      .ipa-fallback {{
        margin-top: 6px;
        font-size: 0.75em;
        opacity: 0.65;
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
          <div class="card-id">#{card_id}</div>
          <div class="badge" style="font-size: {tag_size};">{tag}</div>
          <div class="card-text" style="font-size: {front_size};">{front}</div>
          <div class="hint">Tap card to see English</div>
        </div>
        <div class="flip-card-back">
          <div class="card-id">#{card_id}</div>
          <div class="badge" style="font-size: {tag_size};">{tag}</div>
          {back_content}
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