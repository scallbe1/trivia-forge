import logging
import time

from sqlalchemy import func, select

from .config import get_settings
from .db import Base, SessionLocal, engine
from .models import Question

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("trivia-worker")
settings = get_settings()


def run_ingestion_cycle() -> None:
    """MVP hook for the future hourly knowledge/media ingestion pipeline.

    The first repo milestone intentionally leaves external providers disabled.
    The worker already runs independently so Wikidata/Wikipedia/MusicBrainz/image
    and audio ingestion can be added without changing the deployment topology.
    """
    with SessionLocal() as db:
        question_count = db.scalar(select(func.count(Question.id))) or 0
        log.info("Ingestion cycle complete (provider pipeline not enabled yet). questions=%s", question_count)


def main() -> None:
    Base.metadata.create_all(engine)
    interval = max(60, settings.worker_interval_seconds)
    log.info("Trivia worker started. interval=%ss", interval)
    while True:
        try:
            run_ingestion_cycle()
        except Exception:
            log.exception("Ingestion cycle failed")
        time.sleep(interval)


if __name__ == "__main__":
    main()
