from pathlib import Path
from exerx_eye.db import ExerxEye

CSV = Path(__file__).parents[1] / "data" / "gym_exercise_dataset.csv"

def make_db(tmp_path):
    db = ExerxEye(tmp_path / "test.db")
    assert db.import_csv(CSV) == 617
    return db

def test_import_and_count(tmp_path):
    db = make_db(tmp_path)
    assert db.count() == 617
    assert len(db.distinct("main_muscle")) == 9
    db.close()

def test_search(tmp_path):
    db = make_db(tmp_path)
    rows = db.query(text="barbell", field="Equipment")
    assert rows
    assert all("barbell" in x.equipment.lower() for x in rows)
    db.close()

def test_filters(tmp_path):
    db = make_db(tmp_path)
    rows = db.query(muscle="Chest", difficulty="3")
    assert rows
    assert all(x.main_muscle == "Chest" and x.difficulty == 3 for x in rows)
    db.close()

def test_favorites(tmp_path):
    db = make_db(tmp_path)
    e = db.query(limit=1)[0]
    assert db.toggle_favorite(e.id) is True
    assert db.get(e.id).favorite == 1
    assert db.toggle_favorite(e.id) is False
    db.close()

def test_random(tmp_path):
    db = make_db(tmp_path)
    assert len(db.random("Chest", 6)) == 6
    assert len(db.random_per_main_muscle(1)) == 9
    db.close()
