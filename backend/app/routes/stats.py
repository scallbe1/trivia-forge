from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Attempt, Category, MediaAsset, Question
from ..schemas import StatsSummary

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/summary", response_model=StatsSummary)
def summary(db: Session = Depends(get_db)):
    by_type = {
        row[0]: row[1]
        for row in db.execute(
            select(Question.question_type, func.count(Question.id)).group_by(Question.question_type)
        ).all()
    }
    return StatsSummary(
        questions=db.scalar(select(func.count(Question.id))) or 0,
        categories=db.scalar(select(func.count(Category.id))) or 0,
        media_assets=db.scalar(select(func.count(MediaAsset.id))) or 0,
        attempts=db.scalar(select(func.count(Attempt.id))) or 0,
        by_type=by_type,
    )
