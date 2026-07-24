from typing import Dict, List

CONTENT_TYPES = ("news", "conversation", "talk", "story_telling")
LEVELS = ("easy", "medium", "hard")

# Keyword -> category lookup used to auto-detect 1-3 topic tags per deck.
# Counts are summed per category and the top matches (by hit count) win.
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "food": ["cookie", "cookies", "bake", "baking", "flour", "sugar", "chocolate",
             "recipe", "ingredient", "ingredients", "vanilla", "dough", "oven",
             "biscuit", "biscuits", "cocoa"],
    "manufacturing": ["factory", "factories", "machine", "machinery", "production",
                       "assembly", "conveyor", "industrial", "produce", "produced"],
    "nature": ["forest", "village", "nature", "silence", "northern lights",
               "winter", "mountain", "sweden"],
    "lifestyle": ["life", "journey", "home", "dream", "passion", "moved", "roots"],
    "technology": ["artificial intelligence", "data", "digital", "computing",
                   "technology", "infrastructure", "virtual reality"],
    "government_policy": ["strategy", "government", "policy", "ministry", "governance",
                           "national", "agencies", "officials"],
    "business": ["business", "company", "brand", "employed", "administrator"],
    "family": ["mother", "father", "husband", "family"],
    "art": ["photography", "artist", "paint", "music", "writing", "photographer"],
    "education": ["training", "education", "university", "skills", "students", "majors"],
    "economy": ["economy", "economic", "billion", "million", "percent"],
    "science": ["research", "study", "studies", "brain", "brains", "animal", "animals",
                "monkeys", "rats", "navigation", "surveys", "imaging", "psychology"],
    "advertising": ["phone", "virtual reality", "get that phone", "advertisement",
                    "commercial"],
}

FIRST_PERSON = {"i", "i'm", "my", "me", "myself", "i've", "i'll", "i'd"}
SECOND_PERSON = {"you", "your", "you're", "yours"}
SEQUENCE_CONNECTIVES = {"then", "next", "after", "once", "finally", "first", "soon",
                         "later", "meanwhile"}
FORMAL_WORDS = {"strategy", "government", "governance", "percent", "billion", "million",
                 "policy", "policies", "framework", "national", "officials", "agencies",
                 "ministry", "economy", "digital", "strategic"}