import csv
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

# Accepted CSV column names, mirroring deck_loader.py's aliases, kept here
# (rather than imported) so this module has no dependency on deck_loader.
_VIETNAMESE_COLUMNS = ("vietnamese_text", "vietnamese_meaning")
_ENGLISH_COLUMNS = ("english_text", "english_meaning")

CONTENT_TYPES = ("news", "conversation", "talk", "story_telling")
LEVELS = ("easy", "medium", "hard")

# Keyword -> category lookup used to auto-detect 1-3 topic tags per deck.
# Counts are summed per category and the top matches (by hit count) win.
_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "food": ["cookie", "cookies", "bake", "baking", "flour", "sugar", "chocolate",
             "recipe", "ingredient", "ingredients", "vanilla", "dough", "oven",
             "biscuit", "biscuits", "cocoa"],
    "manufacturing": ["factory", "factories", "machine", "machinery", "production",
                       "assembly", "conveyor", "industrial", "produce", "produced"],
    "nature": ["forest", "village", "nature", "silence", "northern lights",
               "winter", "mountain", "sweden"],
    "lifestyle": ["life", "journey", "home", "dream", "passion", "moved", "roots"],
    "technology": ["ai", "artificial intelligence", "data", "digital", "computing",
                   "technology", "infrastructure"],
    "government_policy": ["strategy", "government", "policy", "ministry", "governance",
                           "national", "agencies", "officials"],
    "business": ["business", "company", "brand", "employed", "administrator"],
    "family": ["mother", "father", "husband", "family"],
    "art": ["photography", "art", "artist", "paint", "music", "writing", "photographer"],
    "education": ["training", "education", "university", "skills", "students", "majors"],
    "economy": ["economy", "economic", "billion", "million", "percent"],
}

_FIRST_PERSON = {"i", "i'm", "my", "me", "myself", "i've", "i'll", "i'd"}
_SECOND_PERSON = {"you", "your", "you're", "yours"}
_SEQUENCE_CONNECTIVES = {"then", "next", "after", "once", "finally", "first", "soon",
                          "later", "meanwhile"}
_FORMAL_WORDS = {"strategy", "government", "governance", "percent", "billion", "million",
                  "policy", "framework", "national", "officials", "agencies", "ministry",
                  "economy", "digital"}


def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _first_present(row: dict, columns) -> str:
    for column in columns:
        if row.get(column):
            return row[column].strip()
    return ""


def _resolve_path(path: Optional[str], default_name: str) -> Path:
    resolved = Path(path) if path else Path(default_name)
    if not resolved.is_absolute():
        resolved = Path(get_project_root()) / resolved
    return resolved


def _split_sentences(text: str) -> List[str]:
    flat = re.sub(r"\s+", " ", text).strip()
    return [s for s in re.split(r"(?<=[.!?])\s+", flat) if s.strip()]


def _count_syllables(word: str) -> int:
    word = word.lower().strip(".,;:!?\"()'")
    if not word:
        return 0
    groups = re.findall(r"[aeiouy]+", word)
    n = len(groups)
    if word.endswith("e") and n > 1:
        n -= 1
    return max(1, n)


def _estimate_level(text: str) -> str:
    """Approximate reading difficulty with a Flesch-Kincaid-style grade
    level (avg sentence length + avg syllables/word), bucketed into
    easy/medium/hard. Purely a heuristic — no external NLP dependency.
    """
    words = text.split()
    if not words:
        return ""
    sentences = _split_sentences(text)
    n_words = len(words)
    n_sentences = max(1, len(sentences))
    avg_sentence_len = n_words / n_sentences
    avg_syllables = sum(_count_syllables(w) for w in words) / n_words
    grade = 0.39 * avg_sentence_len + 11.8 * avg_syllables - 15.59

    if grade < 6:
        return "easy"
    if grade < 13:
        return "medium"
    return "hard"


def _detect_content_type(text: str) -> str:
    """Rule-based content-type classifier using cheap lexical signals:
    first/second-person pronoun density (talk/conversation), question
    density and contractions (conversation), sequential connectives and
    past-tense verbs (story_telling), and formal/institutional vocabulary
    plus numeric density (news). Falls back to "conversation" when no
    signal dominates (e.g. very short text).
    """
    sentences = _split_sentences(text)
    words = text.split()
    n_words = len(words)
    if not n_words:
        return ""
    lower_words = [w.lower().strip(".,;:!\"()") for w in words]

    first_person = sum(1 for w in lower_words if w in _FIRST_PERSON) / n_words
    second_person = sum(1 for w in lower_words if w in _SECOND_PERSON) / n_words
    question_ratio = sum(1 for s in sentences if s.strip().endswith("?")) / max(1, len(sentences))
    contractions = sum(1 for w in words if "'" in w) / n_words
    connectives = sum(1 for w in lower_words if w in _SEQUENCE_CONNECTIVES) / n_words
    formal = sum(1 for w in lower_words if w in _FORMAL_WORDS) / n_words
    past_tense = sum(1 for w in lower_words if w.endswith("ed") and len(w) > 3) / n_words
    numbers = sum(1 for w in words if any(c.isdigit() for c in w) or "%" in w) / n_words

    scores = {
        "news": formal * 5 + numbers * 3,
        "talk": first_person * 4 + second_person * 2,
        "conversation": question_ratio * 4 + contractions * 3 + second_person,
        "story_telling": connectives * 4 + past_tense * 2,
    }
    best_type, best_score = max(scores.items(), key=lambda kv: kv[1])
    if best_score <= 0:
        return "conversation"
    return best_type


def _detect_category_tags(text: str, max_tags: int = 3) -> List[str]:
    """Auto-detect 1-3 topic tags via keyword frequency matching against
    _CATEGORY_KEYWORDS. Falls back to ["general"] if nothing matches."""
    lower_text = text.lower()
    scores = {}
    for category, keywords in _CATEGORY_KEYWORDS.items():
        count = sum(lower_text.count(kw) for kw in keywords)
        if count:
            scores[category] = count
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    tags = [category for category, _ in ranked[:max_tags]]
    return tags or ["general"]


def scan_and_create_metadata(deck_folder: str = "decks", metadata_dir: Optional[str] = None) -> str:
    """Scan every *.csv deck in deck_folder and write one summary row per
    deck to a metadata CSV: deck_id (file name), number of cards, total
    English word count, average English word count per card, and — when a
    matching *.txt source exists in `<deck_folder>/sources/` — an
    auto-detected content_type, level, and 1-3 category_tags.
    """
    decks_dir = _resolve_path(deck_folder, "decks")
    sources_dir = decks_dir / "sources"
    metadata_dir_path = Path(get_project_root()) if not metadata_dir else _resolve_path(metadata_dir, metadata_dir)
    output_csv = metadata_dir_path / "deck_metadata.csv"

    rows = []
    for csv_path in sorted(decks_dir.glob("*.csv")):
        with csv_path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            word_counts = []
            for row in reader:
                vietnamese_text = _first_present(row, _VIETNAMESE_COLUMNS)
                english_text = _first_present(row, _ENGLISH_COLUMNS)
                if not vietnamese_text or not english_text:
                    continue
                word_counts.append(len(english_text.split()))

        num_cards = len(word_counts)
        total_word_count = sum(word_counts)
        avg_word_count = round(total_word_count / num_cards, 2) if num_cards else 0

        content_type = level = ""
        category_tags: List[str] = []
        source_path = sources_dir / f"{csv_path.stem}.txt"
        if source_path.exists():
            source_text = source_path.read_text(encoding="utf-8")
            content_type = _detect_content_type(source_text)
            level = _estimate_level(source_text)
            category_tags = _detect_category_tags(source_text)

        rows.append(
            {
                "deck_id": csv_path.stem,
                "num_cards": num_cards,
                "total_word_count": total_word_count,
                "avg_word_count": avg_word_count,
                "category_tags": ", ".join(category_tags),
                "level": level,  # easy, medium, hard
                "content_type": content_type,  # news, conversation, talk, story_telling
            }
        )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["deck_id", "num_cards", "total_word_count",
                           "avg_word_count",
                           "category_tags", "level", "content_type"]
        )
        writer.writeheader()
        writer.writerows(rows)

    return str(output_csv)


if __name__ == "__main__":
    scan_and_create_metadata(deck_folder="decks", metadata_dir="decks/sources")