from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    parent: Mapped[Category | None] = relationship(remote_side=[id])


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    difficulty_base: Mapped[float] = mapped_column(Float, default=5.0)
    canadian_relevance: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    knowledge_item_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_items.id"), nullable=True)
    primary_category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True, index=True)
    question_type: Mapped[str] = mapped_column(String(50), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    prompt_secondary: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    interesting_fact: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[float] = mapped_column(Float, default=5.0, index=True)
    obscurity: Mapped[float] = mapped_column(Float, default=5.0)
    canadian_relevance: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    era_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    era_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    quality_score: Mapped[float] = mapped_column(Float, default=0.5)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    times_seen: Mapped[int] = mapped_column(Integer, default=0)
    times_correct: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    answers: Mapped[list[Answer]] = relationship(back_populates="question", cascade="all, delete-orphan")
    media_links: Mapped[list[QuestionMedia]] = relationship(back_populates="question", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"
    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    answer_key: Mapped[str] = mapped_column(String(50), default="main")
    answer_text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str] = mapped_column(Text, index=True)
    answer_type: Mapped[str] = mapped_column(String(30), default="canonical")
    points: Mapped[float] = mapped_column(Float, default=1.0)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped[Question] = relationship(back_populates="answers")


class QuestionCategory(Base):
    __tablename__ = "question_categories"
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    type: Mapped[str] = mapped_column(String(40), default="topic", index=True)
    __table_args__ = (UniqueConstraint("name", "type", name="uq_tag_name_type"),)


class QuestionTag(Base):
    __tablename__ = "question_tags"
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(300))
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(200), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class QuestionSource(Base):
    __tablename__ = "question_sources"
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True)
    supports_answer: Mapped[bool] = mapped_column(Boolean, default=True)


class MediaAsset(Base):
    __tablename__ = "media_assets"
    id: Mapped[int] = mapped_column(primary_key=True)
    media_type: Mapped[str] = mapped_column(String(20), index=True)
    role: Mapped[str] = mapped_column(String(30), default="question")
    path: Mapped[str] = mapped_column(Text, unique=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    perceptual_hash: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class QuestionMedia(Base):
    __tablename__ = "question_media"
    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    media_asset_id: Mapped[int] = mapped_column(ForeignKey("media_assets.id", ondelete="CASCADE"), index=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    start_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    reveal_mode: Mapped[str] = mapped_column(String(30), default="full")
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    question: Mapped[Question] = relationship(back_populates="media_links")
    asset: Mapped[MediaAsset] = relationship()


class MusicTrack(Base):
    __tablename__ = "music_tracks"
    id: Mapped[int] = mapped_column(primary_key=True)
    media_asset_id: Mapped[int] = mapped_column(ForeignKey("media_assets.id", ondelete="CASCADE"), unique=True)
    artist: Mapped[str] = mapped_column(String(300), index=True)
    song_title: Mapped[str] = mapped_column(String(300), index=True)
    album: Mapped[str | None] = mapped_column(String(300), nullable=True)
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    genre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    explicit: Mapped[bool] = mapped_column(Boolean, default=False)


class ImageSubject(Base):
    __tablename__ = "image_subjects"
    id: Mapped[int] = mapped_column(primary_key=True)
    media_asset_id: Mapped[int] = mapped_column(ForeignKey("media_assets.id", ondelete="CASCADE"), index=True)
    subject_type: Mapped[str] = mapped_column(String(40), index=True)
    subject_name: Mapped[str] = mapped_column(String(300), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class GameSession(Base):
    __tablename__ = "game_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    game_type: Mapped[str] = mapped_column(String(40), default="practice")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    question_count: Mapped[int] = mapped_column(Integer, default=10)
    difficulty_min: Mapped[float] = mapped_column(Float, default=1.0)
    difficulty_max: Mapped[float] = mapped_column(Float, default=10.0)
    canadian_weight: Mapped[float] = mapped_column(Float, default=0.15)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    max_score: Mapped[float] = mapped_column(Float, default=0.0)
    settings_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class GameQuestion(Base):
    __tablename__ = "game_questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    game_session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True)
    round_number: Mapped[int] = mapped_column(Integer, default=1)
    question_number: Mapped[int] = mapped_column(Integer)
    points: Mapped[float] = mapped_column(Float, default=1.0)
    answered: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (UniqueConstraint("game_session_id", "question_number", name="uq_game_question_number"),)


class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True)
    game_session_id: Mapped[int | None] = mapped_column(ForeignKey("game_sessions.id"), nullable=True, index=True)
    submitted_answer: Mapped[dict[str, Any]] = mapped_column(JSON)
    normalized_answer: Mapped[dict[str, Any]] = mapped_column(JSON)
    points_available: Mapped[float] = mapped_column(Float, default=1.0)
    points_awarded: Mapped[float] = mapped_column(Float, default=0.0)
    correct: Mapped[bool] = mapped_column(Boolean, default=False)
    response_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class QuestionEvent(Base):
    __tablename__ = "question_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    details_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
