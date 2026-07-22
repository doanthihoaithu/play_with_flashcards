import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# Accepted CSV column names for each field, in priority order.
_VIETNAMESE_COLUMNS = ("vietnamese_text", "vietnamese_meaning")
_ENGLISH_COLUMNS = ("english_text", "english_meaning")


@dataclass
class Card:
    key_infor: str
    vietnamese_text: str
    english_text: str


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


def load_decks(decks_dir: Path) -> List[Deck]:
    """Load every *.csv deck file in decks_dir into Deck objects.

    Each row is one card. Expected columns are `key_infor`, a Vietnamese
    column (`vietnamese_text` or `vietnamese_meaning`), and an English column
    (`english_text` or `english_meaning`). Rows missing the Vietnamese or
    English value are skipped; any other columns (e.g. `card_id`) are ignored.
    """
    decks: List[Deck] = []
    if not decks_dir.exists():
        return decks

    for path in sorted(decks_dir.glob("*.csv")):
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            cards = [
                Card(
                    key_infor=(row.get("key_infor") or "").strip(),
                    vietnamese_text=_first_present(row, _VIETNAMESE_COLUMNS),
                    english_text=_first_present(row, _ENGLISH_COLUMNS),
                )
                for row in reader
            ]
            cards = [c for c in cards if c.vietnamese_text and c.english_text]
        if cards:
            decks.append(Deck(name=_deck_name_from_path(path), cards=cards))

    return decks