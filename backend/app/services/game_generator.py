import random
from collections import Counter

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from ..models import GameQuestion, GameSession, Question, QuestionCategory
from ..schemas import GameCreate


def media_family(question_type: str) -> str:
    if question_type.startswith("image_"):
        return "image"
    if question_type.startswith("audio_"):
        return "audio"
    return "text"


def build_game(db: Session, spec: GameCreate) -> GameSession:
    stmt: Select = select(Question).where(
        Question.status == "active",
        Question.difficulty >= spec.difficulty_min,
        Question.difficulty <= spec.difficulty_max,
    )
    if spec.category_ids:
        stmt = stmt.join(
            QuestionCategory, QuestionCategory.question_id == Question.id, isouter=True
        ).where(
            (Question.primary_category_id.in_(spec.category_ids))
            | (QuestionCategory.category_id.in_(spec.category_ids))
        ).distinct()

    candidates = list(db.scalars(stmt).all())
    if not candidates:
        raise ValueError("No active questions match the requested filters")

    random.shuffle(candidates)
    target_counts = {
        "text": round(spec.question_count * spec.text_target),
        "image": round(spec.question_count * spec.image_target),
        "audio": round(spec.question_count * spec.audio_target),
    }
    # Make rounding land exactly on question_count.
    while sum(target_counts.values()) < spec.question_count:
        target_counts["text"] += 1
    while sum(target_counts.values()) > spec.question_count:
        target_counts[max(target_counts, key=target_counts.get)] -= 1

    selected: list[Question] = []
    family_counts: Counter[str] = Counter()
    canadian_goal = round(spec.question_count * spec.canadian_target)
    canadian_count = 0

    def candidate_score(q: Question) -> tuple[float, float]:
        family = media_family(q.question_type)
        family_need = max(0, target_counts[family] - family_counts[family])
        canada_need = max(0, canadian_goal - canadian_count)
        canada_bonus = q.canadian_relevance * canada_need
        return (family_need + canada_bonus, random.random())

    pool = candidates[:]
    while pool and len(selected) < spec.question_count:
        pool.sort(key=candidate_score, reverse=True)
        q = pool.pop(0)
        selected.append(q)
        family_counts[media_family(q.question_type)] += 1
        if q.canadian_relevance >= 0.5:
            canadian_count += 1

    if not selected:
        raise ValueError("Unable to build a game")

    session = GameSession(
        game_type=spec.game_type,
        question_count=len(selected),
        difficulty_min=spec.difficulty_min,
        difficulty_max=spec.difficulty_max,
        canadian_weight=spec.canadian_target,
        settings_json=spec.model_dump(),
    )
    db.add(session)
    db.flush()

    max_score = 0.0
    for number, q in enumerate(selected, start=1):
        keys = {}
        for answer in q.answers:
            keys[answer.answer_key] = max(keys.get(answer.answer_key, 0.0), answer.points)
        points = sum(keys.values()) or 1.0
        max_score += points
        db.add(
            GameQuestion(
                game_session_id=session.id,
                question_id=q.id,
                round_number=1,
                question_number=number,
                points=points,
            )
        )

    session.max_score = max_score
    db.commit()
    db.refresh(session)
    return session
