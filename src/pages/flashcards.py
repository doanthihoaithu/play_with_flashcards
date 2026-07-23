import random
from typing import List

import streamlit as st
import streamlit.components.v1 as components

from card_render import render_card
from config import PROJECT_ROOT, load_config
from deck_selector import select_deck


def new_order(n_cards: int, shuffle: bool) -> list:
    order = list(range(n_cards))
    if shuffle:
        random.shuffle(order)
    return order


config = load_config()
decks_dir = PROJECT_ROOT / config.get("decks_dir", "decks")
default_shuffle = bool(config.get("shuffle_by_default", False))

st.title("Flashcards")

deck, shuffle_on = select_deck(decks_dir, default_shuffle=default_shuffle, key_prefix="flashcards")

# Reset session state whenever the deck or shuffle setting changes.
state_key = (deck.name, shuffle_on)
if st.session_state.get("state_key") != state_key:
    st.session_state.state_key = state_key
    st.session_state.order = new_order(len(deck.cards), shuffle_on)
    st.session_state.pos = 0


@st.fragment
def _render_flashcard_section() -> None:
    # Fragment-scoped: clicking these buttons only reruns this section,
    # not the whole page, so the deck/filter controls above don't
    # re-render and the page doesn't jump/scroll on every click.
    order: List[int] = st.session_state.order
    pos: int = st.session_state.pos
    total = len(order)

    st.caption(f"Card {pos + 1} of {total}")
    st.progress((pos + 1) / total)

    current_card = deck.cards[order[pos]]
    components.html(render_card(current_card), height=300, scrolling=False)

    col_prev, col_shuffle, col_next = st.columns(3)
    with col_prev:
        if st.button("◀ Previous", use_container_width=True, disabled=(pos == 0)):
            st.session_state.pos = max(0, pos - 1)
            st.rerun(scope="fragment")
    with col_shuffle:
        if st.button("\U0001F500 Reshuffle", use_container_width=True):
            st.session_state.order = new_order(len(deck.cards), True)
            st.session_state.pos = 0
            st.rerun(scope="fragment")
    with col_next:
        if st.button("Next ▶", use_container_width=True, disabled=(pos == total - 1)):
            st.session_state.pos = min(total - 1, pos + 1)
            st.rerun(scope="fragment")


_render_flashcard_section()