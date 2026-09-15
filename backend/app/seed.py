from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Answer, Category, Question
from .services.answering import normalize_answer


TOP_LEVEL = [
    ("History & Civilization", "history-civilization"),
    ("World & Geography", "world-geography"),
    ("Arts & Literature", "arts-literature"),
    ("Music", "music"),
    ("Film, TV & Entertainment", "film-tv-entertainment"),
    ("Science & Nature", "science-nature"),
    ("Sports & Games", "sports-games"),
    ("Food & Drink", "food-drink"),
    ("Words, Language & Ideas", "words-language-ideas"),
    ("Culture & Society", "culture-society"),
    ("Technology, Inventions & Business", "technology-business"),
    ("Canada", "canada"),
]


def add_question(db: Session, category: Category, prompt: str, answer: str, *, difficulty: float, canadian: float = 0.0, explanation: str | None = None, question_type: str = "text"):
    q = Question(
        primary_category_id=category.id,
        question_type=question_type,
        prompt=prompt,
        difficulty=difficulty,
        obscurity=difficulty,
        canadian_relevance=canadian,
        quality_score=0.9,
        confidence_score=0.95,
        explanation=explanation,
        status="active",
    )
    q.answers.append(
        Answer(
            answer_key="main",
            answer_text=answer,
            normalized_text=normalize_answer(answer),
            answer_type="canonical",
            points=1.0,
        )
    )
    db.add(q)


def seed_database(db: Session) -> None:
    if db.scalar(select(Category.id).limit(1)):
        return

    cats: dict[str, Category] = {}
    for order, (name, slug) in enumerate(TOP_LEVEL, start=1):
        cat = Category(name=name, slug=slug, sort_order=order)
        db.add(cat)
        db.flush()
        cats[slug] = cat

    # A tiny starter set based on the style of the user's real trivia finals.
    add_question(db, cats["canada"], "What is the capital of Saskatchewan?", "Regina", difficulty=4, canadian=1.0)
    add_question(db, cats["history-civilization"], "Who assassinated Archduke Franz Ferdinand in Sarajevo in 1914?", "Gavrilo Princip", difficulty=6)
    add_question(db, cats["history-civilization"], "What famous embroidered work depicts events leading to the Norman Conquest of England?", "Bayeux Tapestry", difficulty=7)
    add_question(db, cats["words-language-ideas"], "What German loanword means the defining spirit or mood of an age?", "Zeitgeist", difficulty=6)
    add_question(db, cats["culture-society"], "What is the traditional crescent-shaped knife associated with Inuit women called?", "Ulu", difficulty=7, canadian=0.7)
    add_question(db, cats["world-geography"], "What is a U-shaped lake formed when a river meander is cut off from the main channel called?", "Oxbow lake", difficulty=5)
    add_question(db, cats["music"], "Which Bristol trip-hop group released the 1998 album Mezzanine?", "Massive Attack", difficulty=6)
    add_question(db, cats["arts-literature"], "Which Dutch painter created Girl with a Pearl Earring?", "Johannes Vermeer", difficulty=5)
    add_question(db, cats["arts-literature"], "Which author wrote Fahrenheit 451?", "Ray Bradbury", difficulty=4)
    add_question(db, cats["music"], "Which Canadian singer released the hit Greedy in 2023?", "Tate McRae", difficulty=4, canadian=1.0)

    db.commit()
