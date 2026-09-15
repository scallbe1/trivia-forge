from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..models import Attempt, GameQuestion, GameSession, Question, QuestionEvent, QuestionMedia
from ..schemas import AnswerSlot, AttemptCreate, GameCreate, GameOut, GradeResult, MediaOut, PublicQuestion
from ..services.answering import grade_answers
from ..services.game_generator import build_game

router = APIRouter(prefix="/api/games", tags=["games"])


def public_question(q: Question) -> PublicQuestion:
    key_points: dict[str, float] = defaultdict(float)
    for answer in q.answers:
        key_points[answer.answer_key] = max(key_points[answer.answer_key], answer.points)
    slots = [
        AnswerSlot(
            key=key,
            label="Answer" if key == "main" else key.replace("_", " ").title(),
            points=points,
        )
        for key, points in key_points.items()
    ]
    media = [MediaOut.model_validate(link.asset) for link in sorted(q.media_links, key=lambda x: x.display_order)]
    return PublicQuestion(
        id=q.id,
        question_type=q.question_type,
        prompt=q.prompt,
        prompt_secondary=q.prompt_secondary,
        difficulty=q.difficulty,
        canadian_relevance=q.canadian_relevance,
        media=media,
        answer_slots=slots,
    )


def get_game_or_404(db: Session, game_id: int) -> GameSession:
    game = db.get(GameSession, game_id)
    if not game:
        raise HTTPException(404, "Game not found")
    return game


@router.post("", response_model=GameOut, status_code=201)
def create_game(payload: GameCreate, db: Session = Depends(get_db)):
    if payload.difficulty_min > payload.difficulty_max:
        raise HTTPException(400, "difficulty_min cannot exceed difficulty_max")
    try:
        game = build_game(db, payload)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return get_game(game.id, db)


@router.get("/{game_id}", response_model=GameOut)
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = get_game_or_404(db, game_id)
    rows = list(
        db.execute(
            select(GameQuestion, Question)
            .join(Question, Question.id == GameQuestion.question_id)
            .options(
                selectinload(Question.answers),
                selectinload(Question.media_links).selectinload(QuestionMedia.asset),
            )
            .where(GameQuestion.game_session_id == game_id)
            .order_by(GameQuestion.question_number)
        ).all()
    )
    return GameOut(
        id=game.id,
        game_type=game.game_type,
        score=game.score,
        max_score=game.max_score,
        question_count=game.question_count,
        questions=[public_question(q) for _, q in rows],
    )


@router.post("/{game_id}/answer", response_model=GradeResult)
def submit_answer(game_id: int, payload: AttemptCreate, db: Session = Depends(get_db)):
    game = get_game_or_404(db, game_id)
    game_question = db.scalar(
        select(GameQuestion).where(
            GameQuestion.game_session_id == game_id,
            GameQuestion.question_id == payload.question_id,
        )
    )
    if not game_question:
        raise HTTPException(400, "Question is not part of this game")
    if game_question.answered:
        raise HTTPException(409, "Question has already been answered")

    question = db.scalar(select(Question).options(selectinload(Question.answers)).where(Question.id == payload.question_id))
    if not question:
        raise HTTPException(404, "Question not found")

    awarded, available, correct, canonical, normalized = grade_answers(question.answers, payload.answers)
    db.add(
        Attempt(
            question_id=question.id,
            game_session_id=game.id,
            submitted_answer=payload.answers,
            normalized_answer=normalized,
            points_available=available,
            points_awarded=awarded,
            correct=correct,
            response_seconds=payload.response_seconds,
        )
    )
    game_question.answered = True
    game.score += awarded
    question.times_seen += 1
    if correct:
        question.times_correct += 1
    db.add(
        QuestionEvent(
            question_id=question.id,
            event_type="answered_correct" if correct else "answered_wrong",
            details_json={"game_id": game.id, "points": awarded},
        )
    )
    db.commit()

    return GradeResult(
        correct=correct,
        points_awarded=awarded,
        points_available=available,
        canonical_answers=canonical,
        explanation=question.explanation,
        interesting_fact=question.interesting_fact,
    )
