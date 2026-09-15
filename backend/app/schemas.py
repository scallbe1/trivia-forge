from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CategoryOut(ORMModel):
    id: int
    parent_id: int | None
    name: str
    slug: str
    description: str | None
    sort_order: int
    active: bool


class CategoryCreate(BaseModel):
    parent_id: int | None = None
    name: str
    slug: str
    description: str | None = None
    sort_order: int = 0


class AnswerCreate(BaseModel):
    answer_key: str = "main"
    answer_text: str
    answer_type: str = "canonical"
    points: float = 1.0
    required: bool = True
    sort_order: int = 0


class AnswerOut(ORMModel):
    id: int
    answer_key: str
    answer_text: str
    normalized_text: str
    answer_type: str
    points: float
    required: bool
    sort_order: int


class MediaOut(ORMModel):
    id: int
    media_type: str
    role: str
    path: str
    mime_type: str | None
    width: int | None
    height: int | None
    duration_seconds: float | None
    title: str | None
    description: str | None
    created_at: datetime

    @property
    def url(self) -> str:
        return f"/media/{self.path}"


class QuestionMediaOut(BaseModel):
    id: int
    media_asset_id: int
    display_order: int
    start_seconds: float | None
    duration_seconds: float | None
    reveal_mode: str
    metadata_json: dict[str, Any] | None
    asset: MediaOut

    model_config = ConfigDict(from_attributes=True)


class MediaClipCreate(BaseModel):
    start_seconds: float = Field(default=0.0, ge=0)
    duration_seconds: float = Field(default=12.0, ge=1, le=60)
    normalize: bool = True
    fade: bool = True


class QuestionCreate(BaseModel):
    primary_category_id: int | None = None
    knowledge_item_id: int | None = None
    question_type: str = "text"
    prompt: str
    prompt_secondary: str | None = None
    explanation: str | None = None
    interesting_fact: str | None = None
    difficulty: float = Field(default=5.0, ge=1, le=10)
    obscurity: float = Field(default=5.0, ge=1, le=10)
    canadian_relevance: float = Field(default=0.0, ge=0, le=1)
    status: str = "active"
    answers: list[AnswerCreate]


class QuestionOut(ORMModel):
    id: int
    primary_category_id: int | None
    knowledge_item_id: int | None
    question_type: str
    prompt: str
    prompt_secondary: str | None
    explanation: str | None
    interesting_fact: str | None
    difficulty: float
    obscurity: float
    canadian_relevance: float
    status: str
    quality_score: float
    confidence_score: float
    times_seen: int
    times_correct: int
    answers: list[AnswerOut] = Field(default_factory=list)
    media_links: list[QuestionMediaOut] = Field(default_factory=list)


class AnswerSlot(BaseModel):
    key: str
    label: str
    points: float


class PublicQuestion(BaseModel):
    id: int
    question_type: str
    prompt: str
    prompt_secondary: str | None
    difficulty: float
    canadian_relevance: float
    media: list[MediaOut]
    answer_slots: list[AnswerSlot]


class GameCreate(BaseModel):
    game_type: str = "practice"
    question_count: int = Field(default=10, ge=1, le=200)
    difficulty_min: float = Field(default=1.0, ge=1, le=10)
    difficulty_max: float = Field(default=10.0, ge=1, le=10)
    canadian_target: float = Field(default=0.15, ge=0, le=1)
    text_target: float = Field(default=0.60, ge=0, le=1)
    image_target: float = Field(default=0.20, ge=0, le=1)
    audio_target: float = Field(default=0.20, ge=0, le=1)
    category_ids: list[int] = Field(default_factory=list)


class GameOut(BaseModel):
    id: int
    game_type: str
    score: float
    max_score: float
    question_count: int
    questions: list[PublicQuestion]


class AttemptCreate(BaseModel):
    question_id: int
    answers: dict[str, str]
    response_seconds: float | None = None


class GradeResult(BaseModel):
    correct: bool
    points_awarded: float
    points_available: float
    canonical_answers: dict[str, str]
    explanation: str | None
    interesting_fact: str | None


class StatsSummary(BaseModel):
    questions: int
    categories: int
    media_assets: int
    attempts: int
    by_type: dict[str, int]
