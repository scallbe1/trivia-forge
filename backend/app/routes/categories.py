from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Category
from ..schemas import CategoryCreate, CategoryOut

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return list(db.scalars(select(Category).order_by(Category.sort_order, Category.name)).all())


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Category).where(Category.slug == payload.slug)):
        raise HTTPException(409, "Category slug already exists")
    row = Category(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
