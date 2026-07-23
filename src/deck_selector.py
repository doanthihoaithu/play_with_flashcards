"""Shared deck-selection UI: filters (content type / level / category tags)
plus the deck picker. Used by both the Flashcards and Shadowing pages so
deck selection behaves identically everywhere.
"""
import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple

import streamlit as st

from deck_loader import Deck, load_decks


@st.cache_data(show_spinner=False)
def _load_decks_cached(decks_dir: Path) -> List[Deck]:
    """Cache deck parsing across reruns — Streamlit reruns the whole script
    on every interaction, and the CSV files don't change during a session."""
    return load_decks(decks_dir)


def _normalize_deck_key(name: str) -> str:
    """Normalize a deck name/id so "How_Oreo_Cookies" and "How Oreo Cookies"
    (title-cased or not) compare equal, for matching Deck.name to deck_id."""
    return re.sub(r"[_\-\s]+", " ", name).strip().lower()


@st.cache_data(show_spinner=False)
def _load_deck_metadata(metadata_path: Path) -> Dict[str, dict]:
    """Load deck_metadata.csv (produced by utils.scan_and_create_metadata)
    into {normalized_deck_key: {content_type, level, category_tags}}.
    Returns {} if the file doesn't exist — filters simply won't appear."""
    if not metadata_path.exists():
        return {}

    metadata: Dict[str, dict] = {}
    with metadata_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            deck_id = (row.get("deck_id") or "").strip()
            if not deck_id:
                continue
            tags = [t.strip() for t in (row.get("category_tags") or "").split(",") if t.strip()]
            metadata[_normalize_deck_key(deck_id)] = {
                "content_type": (row.get("content_type") or "").strip(),
                "level": (row.get("level") or "").strip(),
                "category_tags": tags,
            }
    return metadata


def select_deck(
    decks_dir: Path,
    *,
    default_shuffle: bool = False,
    show_shuffle: bool = True,
    key_prefix: str = "",
) -> Tuple[Deck, bool]:
    """Render the shared filters + deck picker (+ optional shuffle checkbox)
    and return (selected_deck, shuffle_on). Stops the script (st.stop()) if
    there are no decks at all, or none match the selected filters.

    key_prefix scopes widget keys so this can be called from multiple pages
    in the same app session without their filter/deck selections colliding.
    """
    decks = _load_decks_cached(decks_dir)
    if not decks:
        st.warning(
            f"No decks found in `{decks_dir}`. Add a `*.csv` file there with "
            "columns `key_infor`, `vietnamese_text`, and `english_text`."
        )
        st.stop()

    metadata_path = decks_dir / "sources" / "deck_metadata.csv"
    deck_metadata = _load_deck_metadata(metadata_path)
    deck_meta_list = [deck_metadata.get(_normalize_deck_key(d.name), {}) for d in decks]

    content_type_options = sorted({m["content_type"] for m in deck_meta_list if m.get("content_type")})
    level_options = sorted({m["level"] for m in deck_meta_list if m.get("level")})
    tag_options = sorted({tag for m in deck_meta_list for tag in m.get("category_tags", [])})

    st.subheader("Decks")

    selected_content_types: List[str] = []
    selected_levels: List[str] = []
    selected_tags: List[str] = []
    if content_type_options or level_options or tag_options:
        st.markdown("**Filters**")
        filter_cols = st.columns(3)
        if content_type_options:
            with filter_cols[0]:
                selected_content_types = st.multiselect(
                    "Content type", content_type_options, key=f"{key_prefix}_content_type"
                )
        if level_options:
            with filter_cols[1]:
                selected_levels = st.multiselect(
                    "Level", level_options, key=f"{key_prefix}_level"
                )
        if tag_options:
            with filter_cols[2]:
                selected_tags = st.multiselect(
                    "Category tags", tag_options, key=f"{key_prefix}_tags"
                )

    def _matches_filters(meta: dict) -> bool:
        if not meta:
            return not (selected_content_types or selected_levels or selected_tags)
        if selected_content_types and meta.get("content_type") not in selected_content_types:
            return False
        if selected_levels and meta.get("level") not in selected_levels:
            return False
        if selected_tags and not set(meta.get("category_tags", [])) & set(selected_tags):
            return False
        return True

    filtered_decks = [d for d, meta in zip(decks, deck_meta_list) if _matches_filters(meta)]

    if not filtered_decks:
        st.warning("No decks match the selected filters.")
        st.stop()

    deck_names = [d.name for d in filtered_decks]
    if show_shuffle:
        deck_col, shuffle_col = st.columns([3, 1])
        with deck_col:
            selected_name = st.selectbox(
                "Choose a deck to study", deck_names, key=f"{key_prefix}_deck"
            )
        with shuffle_col:
            st.markdown("<br>", unsafe_allow_html=True)
            shuffle_on = st.checkbox(
                "Shuffle cards", value=default_shuffle, key=f"{key_prefix}_shuffle"
            )
    else:
        selected_name = st.selectbox(
            "Choose a deck to study", deck_names, key=f"{key_prefix}_deck"
        )
        shuffle_on = False

    deck = next(d for d in filtered_decks if d.name == selected_name)
    return deck, shuffle_on