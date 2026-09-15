import re
import unicodedata
from collections import defaultdict

from ..models import Answer


LEADING_ARTICLES = ("the ", "a ", "an ")


def normalize_answer(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold().strip()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value).strip()
    for article in LEADING_ARTICLES:
        if value.startswith(article):
            value = value[len(article):]
            break
    return value


def grade_answers(answer_rows: list[Answer], submitted: dict[str, str]) -> tuple[float, float, bool, dict[str, str], dict[str, str]]:
    groups: dict[str, list[Answer]] = defaultdict(list)
    for row in answer_rows:
        groups[row.answer_key].append(row)

    points_awarded = 0.0
    points_available = 0.0
    canonical: dict[str, str] = {}
    normalized_submission: dict[str, str] = {}
    required_correct = True

    for key, rows in groups.items():
        max_points = max((r.points for r in rows), default=0.0)
        points_available += max_points
        canonical_row = next((r for r in rows if r.answer_type == "canonical"), rows[0])
        canonical[key] = canonical_row.answer_text

        supplied = normalize_answer(submitted.get(key, ""))
        normalized_submission[key] = supplied
        accepted = {r.normalized_text for r in rows if r.answer_type in {"canonical", "alias", "alternate"}}
        matched = supplied in accepted and bool(supplied)
        if matched:
            points_awarded += max_points
        elif any(r.required for r in rows):
            required_correct = False

    correct = required_correct and abs(points_awarded - points_available) < 1e-9
    return points_awarded, points_available, correct, canonical, normalized_submission
