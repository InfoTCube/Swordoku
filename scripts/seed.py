"""
Seed the database with 10 puzzles per difficulty (30 total).
Idempotent: counts existing puzzles per difficulty and only inserts what is missing.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session


from backend.core.database import SessionLocal
from backend.models.puzzle import Puzzle
from backend.services.difficulty_classifier import classify_difficulty
from backend.services.puzzle_generator import generate_solved_grid, make_puzzle

PUZZLES_PER_DIFFICULTY = 10
DIFFICULTIES = ["easy", "medium", "hard"]
MAX_ATTEMPTS_MULTIPLIER = 20


def seed(db: Session) -> None:
    for difficulty in DIFFICULTIES:
        existing = db.query(Puzzle).filter(Puzzle.difficulty == difficulty).count()
        needed = PUZZLES_PER_DIFFICULTY - existing
        if needed <= 0:
            print(f"[seed] {difficulty}: {existing} puzzles already present, skipping")
            continue

        print(f"[seed] {difficulty}: generating {needed} puzzle(s)...")
        generated = 0
        attempts = 0
        max_attempts = needed * MAX_ATTEMPTS_MULTIPLIER

        while generated < needed:
            if attempts >= max_attempts:
                print(
                    f"[seed] {difficulty}: reached attempt limit, inserted {generated}/{needed}"
                )
                break
            attempts += 1

            solved = generate_solved_grid()
            givens, solution = make_puzzle(solved, difficulty)
            actual = classify_difficulty(givens)
            if actual.value != difficulty:
                continue

            db.add(Puzzle(difficulty=difficulty, givens=givens, solution=solution))
            generated += 1

        if generated > 0:
            db.commit()
        print(f"[seed] {difficulty}: done ({generated} inserted, {attempts} attempts)")


def main() -> None:
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    print("[seed] Seeding complete.")


if __name__ == "__main__":
    main()
