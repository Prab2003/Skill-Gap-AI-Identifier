# resume_parser.py  –  Extract skills from resume text via keyword matching

from __future__ import annotations
import re
from typing import Dict
from config import SKILL_ALIASES


def extract_skills_from_text(text: str) -> Dict[str, int]:
    """Scan *text* for known skill keywords and return a dict of
    ``{skill_name: estimated_level}`` (1-10).

    Proficiency heuristic
    ---------------------
    * base level = 4  (mentioned at least once → you know it)
    * +1 for each additional distinct alias found (capped at 8)
    * Presence of "senior", "lead", "expert", "advanced" near the
      keyword nudges the level up.
    """
    if not text:
        return {}

    text_lower = text.lower()
    found: Dict[str, int] = {}

    boost_words = {"senior", "lead", "expert", "advanced", "extensive", "proficient", "strong"}
    has_boost = bool(boost_words & set(re.findall(r"\b\w+\b", text_lower)))

    for skill, aliases in SKILL_ALIASES.items():
        matched_aliases = sum(1 for a in aliases if a in text_lower)
        if matched_aliases > 0:
            level = min(8, 4 + matched_aliases - 1)
            if has_boost:
                level = min(9, level + 1)
            found[skill] = level

    return found
