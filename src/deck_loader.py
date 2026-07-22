from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


@dataclass
class Card:
    key_infor: str
    vietnamese_text: str
    english_text: str


@dataclass
class Deck:
    name: str
    cards: List[Card] = field(default_factory=list)


def load_decks(decks_dir: Path) -> List[Deck]:
    """Load every *.yaml deck file in decks_dir into Deck objects.

    Files that are missing required fields or contain no cards are skipped.
    """
    decks: List[Deck] = []
    if not decks_dir.exists():
        return decks

    for path in sorted(decks_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        raw_cards = data.get("cards") or []
        cards = [
            Card(
                key_infor=str(c.get("key_infor", "")),
                vietnamese_text=str(c.get("vietnamese_text", "")),
                english_text=str(c.get("english_text", "")),
            )
            for c in raw_cards
            if c.get("vietnamese_text") and c.get("english_text")
        ]
        if cards:
            decks.append(Deck(name=data.get("name", path.stem), cards=cards))

    return decks