from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..models import Answer, Question, QuestionEvent, QuestionMedia
from ..schemas import QuestionCreate, QuestionOut
from ..services.answering import normalize_answer

router = APIRouter(prefix="/api/questions", tags=["questions"])


def question_stmt():
    return select(Question).options(
        selectinload(Question.answers),
        selectinload(Question.media_links).selectinload(QuestionMedia.asset),
    )


@router.get("", response_model=list[QuestionOut])
def list_questions(
    question_type: str | None = None,
    status: str | None = "active",
    category_id: int | None = None,
    difficulty_min: float | None = Query(default=None, ge=1, le=10),
    difficulty_max: float | None = Query(default=None, ge=1, le=10),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    stmt = question_stmt()
    if question_type:
        stmt = stmt.where(Question.question_type == question_type)
    if status:
        stmt = stmt.where(Question.status == status)
    if category_id:
        stmt = stmt.where(Question.primary_category_id == category_id)
    if difficulty_min is not None:
        stmt = stmt.where(Question.difficulty >= difficulty_min)
    if difficulty_max is not None:
        stmt = stmt.where(Question.difficulty <= difficulty_max)
    stmt = stmt.order_by(Question.id.desc()).limit(limit)
    return list(db.scalars(stmt).unique().all())


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(question_id: int, db: Session = Depends(get_db)):
    row = db.scalar(question_stmt().where(Question.id == question_id))
    if not row:
        raise HTTPException(404, "Question not found")
    return row


@router.post("", response_model=QuestionOut, status_code=201)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude={"answers"})
    row = Question(**data)
    for answer in payload.answers:
        row.answers.append(
            Answer(
                **answer.model_dump(),
                normalized_text=normalize_answer(answer.answer_text),
            )
        )
    db.add(row)
    db.flush()
    db.add(QuestionEvent(question_id=row.id, event_type="created", details_json={"source": "api"}))
    db.commit()
    return get_question(row.id, db)
