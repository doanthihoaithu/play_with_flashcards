import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Accepted CSV column names for each field, in priority order.
_VIETNAMESE_COLUMNS = ("vietnamese_text", "vietnamese_meaning")
_ENGLISH_COLUMNS = ("english_text", "english_meaning")

_WORD_TOKEN_DELIMITER = "___"


@dataclass
class Card:
    card_id: str
    key_infor: str
    vietnamese_text: str
    english_text: str
    english_ipa: str = ""
    word_ipa_pairs: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class Deck:
    name: str
    cards: List[Card] = field(default_factory=list)


def _first_present(row: dict, columns) -> str:
    for column in columns:
        if row.get(column):
            return row[column].strip()
    return ""


def _deck_name_from_path(path: Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ").strip().title()


def _build_word_ipa_pairs(row: dict) -> List[Tuple[str, str]]:
    """Pair up english_meaning_separated_by_space and english_ipa_separated_by_space.

    Both columns are "___"-joined and word-aligned by construction. Bold
    (**) markers already present in the word tokens are preserved as-is —
    rendering decides what to do with them.
    """
    words_raw = (row.get("english_meaning_separated_by_space") or "").strip()
    ipas_raw = (row.get("english_ipa_separated_by_space") or "").strip()
    if not words_raw or not ipas_raw:
        return []

    words = words_raw.split(_WORD_TOKEN_DELIMITER)
    ipas = ipas_raw.split(_WORD_TOKEN_DELIMITER)
    if len(words) != len(ipas):
        logger.warning(
            "word/IPA token count mismatch (%d words vs %d IPA chunks) — padding shorter list",
            len(words), len(ipas),
        )
        target_len = max(len(words), len(ipas))
        words += [""] * (target_len - len(words))
        ipas += [""] * (target_len - len(ipas))

    return list(zip(words, ipas))


def load_decks(decks_dir: Path) -> List[Deck]:
    """Load every *.csv deck file in decks_dir into Deck objects.

    Each row is one card. Expected columns are `key_infor`, a Vietnamese
    column (`vietnamese_text` or `vietnamese_meaning`), and an English column
    (`english_text` or `english_meaning`). A `card_id` column is used if
    present; otherwise cards are numbered by their row position. Rows missing
    the Vietnamese or English value are skipped.
    """
    decks: List[Deck] = []
    if not decks_dir.exists():
        return decks

    for path in sorted(decks_dir.glob("*.csv")):
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            cards = [
                Card(
                    card_id=(row.get("card_id") or "").strip() or str(i),
                    key_infor=(row.get("key_infor") or "").strip(),
                    vietnamese_text=_first_present(row, _VIETNAMESE_COLUMNS),
                    english_text=_first_present(row, _ENGLISH_COLUMNS),
                    english_ipa=(row.get("english_ipa") or "").strip(),
                    word_ipa_pairs=_build_word_ipa_pairs(row),
                )
                for i, row in enumerate(reader, start=1)
            ]
            cards = [c for c in cards if c.vietnamese_text and c.english_text]
        if cards:
            decks.append(Deck(name=_deck_name_from_path(path), cards=cards))

    return decks