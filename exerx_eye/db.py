from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

CSV_COLUMNS = [
    "Exercise Name", "Equipment", "Variation", "Utility", "Mechanics", "Force",
    "Preparation", "Execution", "Target_Muscles", "Synergist_Muscles",
    "Stabilizer_Muscles", "Antagonist_Muscles", "Dynamic_Stabilizer_Muscles",
    "Main_muscle", "Difficulty (1-5)", "Secondary Muscles", "parent_id",
]

DB_COLUMNS = [
    "exercise_name", "equipment", "variation", "utility", "mechanics", "force",
    "preparation", "execution", "target_muscles", "synergist_muscles",
    "stabilizer_muscles", "antagonist_muscles", "dynamic_stabilizer_muscles",
    "main_muscle", "difficulty", "secondary_muscles", "parent_id",
]

SEARCHABLE = {
    "All": None,
    "Name": "exercise_name",
    "Equipment": "equipment",
    "Target": "target_muscles",
    "Main Muscle": "main_muscle",
    "Utility": "utility",
    "Mechanics": "mechanics",
    "Force": "force",
    "Variation": "variation",
}

@dataclass(slots=True)
class Exercise:
    id: int
    exercise_name: str
    equipment: str
    variation: str
    utility: str
    mechanics: str
    force: str
    preparation: str
    execution: str
    target_muscles: str
    synergist_muscles: str
    stabilizer_muscles: str
    antagonist_muscles: str
    dynamic_stabilizer_muscles: str
    main_muscle: str
    difficulty: int
    secondary_muscles: str
    parent_id: str
    favorite: int = 0

class ExerxEye:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    def close(self) -> None:
        self.conn.close()

    def _create_schema(self) -> None:
        self.conn.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY,
            exercise_name TEXT NOT NULL,
            equipment TEXT NOT NULL DEFAULT '',
            variation TEXT NOT NULL DEFAULT '',
            utility TEXT NOT NULL DEFAULT '',
            mechanics TEXT NOT NULL DEFAULT '',
            force TEXT NOT NULL DEFAULT '',
            preparation TEXT NOT NULL DEFAULT '',
            execution TEXT NOT NULL DEFAULT '',
            target_muscles TEXT NOT NULL DEFAULT '',
            synergist_muscles TEXT NOT NULL DEFAULT '',
            stabilizer_muscles TEXT NOT NULL DEFAULT '',
            antagonist_muscles TEXT NOT NULL DEFAULT '',
            dynamic_stabilizer_muscles TEXT NOT NULL DEFAULT '',
            main_muscle TEXT NOT NULL DEFAULT '',
            difficulty INTEGER NOT NULL DEFAULT 0 CHECK(difficulty BETWEEN 0 AND 5),
            secondary_muscles TEXT NOT NULL DEFAULT '',
            parent_id TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS favorites (
            exercise_id INTEGER PRIMARY KEY REFERENCES exercises(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS workout_exercises (
            id INTEGER PRIMARY KEY,
            workout_id INTEGER NOT NULL REFERENCES workouts(id) ON DELETE CASCADE,
            exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
            position INTEGER NOT NULL DEFAULT 0, sets INTEGER NOT NULL DEFAULT 3,
            reps INTEGER NOT NULL DEFAULT 10, target_weight REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS workout_sessions (
            id INTEGER PRIMARY KEY, workout_id INTEGER REFERENCES workouts(id) ON DELETE SET NULL,
            workout_name TEXT NOT NULL, started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS workout_sets (
            id INTEGER PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
            exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
            set_number INTEGER NOT NULL, reps INTEGER NOT NULL, weight REAL NOT NULL DEFAULT 0,
            completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_workout_exercises_workout ON workout_exercises(workout_id, position);
        CREATE INDEX IF NOT EXISTS idx_workout_sets_exercise ON workout_sets(exercise_id);
        CREATE INDEX IF NOT EXISTS idx_exercises_name ON exercises(exercise_name);
        CREATE INDEX IF NOT EXISTS idx_exercises_equipment ON exercises(equipment);
        CREATE INDEX IF NOT EXISTS idx_exercises_main_muscle ON exercises(main_muscle);
        CREATE INDEX IF NOT EXISTS idx_exercises_difficulty ON exercises(difficulty);
        """)
        self.conn.execute("INSERT OR IGNORE INTO schema_migrations(version,name) VALUES(1,'base_exercise_schema')")
        self.conn.execute("INSERT OR IGNORE INTO schema_migrations(version,name) VALUES(2,'workout_tracking')")
        self.conn.execute("INSERT OR IGNORE INTO schema_migrations(version,name) VALUES(3,'analytics_and_health')")
        self.conn.commit()

    def schema_version(self) -> int:
        row = self.conn.execute("SELECT COALESCE(MAX(version),0) FROM schema_migrations").fetchone()
        return int(row[0])

    def session_set_count(self, session_id: int, exercise_id: int) -> int:
        return int(self.conn.execute(
            "SELECT COUNT(*) FROM workout_sets WHERE session_id=? AND exercise_id=?",
            (session_id, exercise_id),
        ).fetchone()[0])

    def import_csv(self, csv_path: Path, replace: bool = False) -> int:
        if self.count() and not replace:
            return 0
        with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            missing = [c for c in CSV_COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                raise ValueError(f"CSV missing columns: {', '.join(missing)}")
            rows = []
            for r in reader:
                vals = [(r.get(c) or "").strip() for c in CSV_COLUMNS]
                try:
                    vals[14] = int(float(vals[14])) if vals[14] else 0
                except ValueError:
                    vals[14] = 0
                rows.append(vals)
        with self.conn:
            if replace:
                self.conn.execute("DELETE FROM favorites")
                self.conn.execute("DELETE FROM exercises")
            self.conn.executemany(
                f"INSERT INTO exercises ({','.join(DB_COLUMNS)}) VALUES ({','.join('?' for _ in DB_COLUMNS)})",
                rows,
            )
        return len(rows)

    def count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM exercises").fetchone()[0])

    def query(self, *, text: str = "", field: str = "All", equipment: str = "All",
              muscle: str = "All", difficulty: str = "All", favorites_only: bool = False,
              limit: int = 500) -> list[Exercise]:
        clauses, params = [], []
        text = text.strip()
        if text:
            # Query language examples: muscle:Chest equipment:Dumbbell -force:Pull difficulty:3
            terms = []
            field_map = {
                "muscle": "main_muscle", "equipment": "equipment", "force": "force",
                "mechanics": "mechanics", "utility": "utility", "name": "exercise_name",
                "target": "target_muscles", "difficulty": "difficulty",
            }
            for token in text.split():
                neg = token.startswith("-")
                raw = token[1:] if neg else token
                if ":" in raw:
                    key, value = raw.split(":", 1)
                    col = field_map.get(key.lower())
                    if col and value:
                        op = "NOT LIKE" if neg else "LIKE"
                        if col == "difficulty" and value.isdigit():
                            clauses.append(f"e.{col} {'!=' if neg else '='} ?")
                            params.append(int(value))
                        else:
                            clauses.append(f"LOWER(e.{col}) {op} ?")
                            params.append(f"%{value.lower()}%")
                        continue
                terms.append(token)
            plain = " ".join(terms).strip()
            if plain:
                col = SEARCHABLE.get(field)
                if col:
                    clauses.append(f"LOWER(e.{col}) LIKE ?")
                    params.append(f"%{plain.lower()}%")
                else:
                    cols = [c for c in DB_COLUMNS if c != "difficulty"]
                    clauses.append("(" + " OR ".join(f"LOWER(e.{c}) LIKE ?" for c in cols) + ")")
                    params.extend([f"%{plain.lower()}%"] * len(cols))
        if equipment != "All":
            clauses.append("e.equipment = ?")
            params.append(equipment)
        if muscle != "All":
            clauses.append("e.main_muscle = ?")
            params.append(muscle)
        if difficulty != "All":
            clauses.append("e.difficulty = ?")
            params.append(int(difficulty))
        if favorites_only:
            clauses.append("f.exercise_id IS NOT NULL")
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"""
          SELECT e.*, CASE WHEN f.exercise_id IS NULL THEN 0 ELSE 1 END AS favorite
          FROM exercises e LEFT JOIN favorites f ON f.exercise_id=e.id
          {where} ORDER BY e.main_muscle, e.exercise_name, e.equipment LIMIT ?
        """
        params.append(limit)
        return [Exercise(**dict(r)) for r in self.conn.execute(sql, params).fetchall()]

    def get(self, exercise_id: int) -> Exercise | None:
        row = self.conn.execute("""
          SELECT e.*, CASE WHEN f.exercise_id IS NULL THEN 0 ELSE 1 END AS favorite
          FROM exercises e LEFT JOIN favorites f ON f.exercise_id=e.id WHERE e.id=?
        """, (exercise_id,)).fetchone()
        return Exercise(**dict(row)) if row else None

    def distinct(self, column: str) -> list[str]:
        if column not in {"equipment", "main_muscle", "target_muscles", "utility", "mechanics", "force"}:
            raise ValueError("Unsupported distinct column")
        rows = self.conn.execute(
            f"SELECT DISTINCT {column} FROM exercises WHERE {column} <> '' ORDER BY {column} COLLATE NOCASE"
        ).fetchall()
        return [r[0] for r in rows]

    def random(self, muscle: str | None = None, count: int = 1) -> list[Exercise]:
        where, params = "", []
        if muscle and muscle != "All":
            where = "WHERE LOWER(e.target_muscles) LIKE ? OR e.main_muscle = ?"
            params = [f"%{muscle.lower()}%", muscle]
        params.append(count)
        rows = self.conn.execute(f"""
          SELECT e.*, CASE WHEN f.exercise_id IS NULL THEN 0 ELSE 1 END AS favorite
          FROM exercises e LEFT JOIN favorites f ON f.exercise_id=e.id
          {where} ORDER BY RANDOM() LIMIT ?
        """, params).fetchall()
        return [Exercise(**dict(r)) for r in rows]

    def random_per_main_muscle(self, count_each: int = 1) -> list[Exercise]:
        result: list[Exercise] = []
        for muscle in self.distinct("main_muscle"):
            rows = self.conn.execute("""
              SELECT e.*, CASE WHEN f.exercise_id IS NULL THEN 0 ELSE 1 END AS favorite
              FROM exercises e LEFT JOIN favorites f ON f.exercise_id=e.id
              WHERE e.main_muscle=? ORDER BY RANDOM() LIMIT ?
            """, (muscle, count_each)).fetchall()
            result.extend(Exercise(**dict(r)) for r in rows)
        return result

    def toggle_favorite(self, exercise_id: int) -> bool:
        exists = self.conn.execute("SELECT 1 FROM favorites WHERE exercise_id=?", (exercise_id,)).fetchone()
        with self.conn:
            if exists:
                self.conn.execute("DELETE FROM favorites WHERE exercise_id=?", (exercise_id,))
                return False
            self.conn.execute("INSERT INTO favorites(exercise_id) VALUES(?)", (exercise_id,))
            return True

    def create_workout(self, name: str, notes: str = "") -> int:
        name=name.strip()
        if not name: raise ValueError("Workout name is required")
        with self.conn:
            cur=self.conn.execute("INSERT INTO workouts(name,notes) VALUES(?,?)",(name,notes.strip()))
        return int(cur.lastrowid)

    def list_workouts(self):
        return self.conn.execute("""SELECT w.id,w.name,w.notes,w.created_at,COUNT(we.id) exercise_count
            FROM workouts w LEFT JOIN workout_exercises we ON we.workout_id=w.id
            GROUP BY w.id ORDER BY w.id DESC""").fetchall()

    def add_to_workout(self, workout_id:int, exercise_id:int, sets:int=3, reps:int=10, target_weight:float=0):
        pos=self.conn.execute("SELECT COALESCE(MAX(position),0)+1 FROM workout_exercises WHERE workout_id=?",(workout_id,)).fetchone()[0]
        with self.conn:
            self.conn.execute("""INSERT INTO workout_exercises
                (workout_id,exercise_id,position,sets,reps,target_weight) VALUES(?,?,?,?,?,?)""",
                (workout_id,exercise_id,pos,sets,reps,target_weight))

    def workout_detail(self, workout_id:int):
        return self.conn.execute("""SELECT we.id item_id,we.position,we.sets,we.reps,we.target_weight,
            e.id exercise_id,e.exercise_name,e.main_muscle,e.equipment
            FROM workout_exercises we JOIN exercises e ON e.id=we.exercise_id
            WHERE we.workout_id=? ORDER BY we.position,we.id""",(workout_id,)).fetchall()

    def start_session(self, workout_id:int)->int:
        w=self.conn.execute("SELECT name FROM workouts WHERE id=?",(workout_id,)).fetchone()
        if not w: raise ValueError("Workout not found")
        with self.conn:
            cur=self.conn.execute("INSERT INTO workout_sessions(workout_id,workout_name) VALUES(?,?)",(workout_id,w["name"]))
        return int(cur.lastrowid)

    def log_set(self, session_id:int, exercise_id:int, set_number:int, reps:int, weight:float=0)->int:
        with self.conn:
            cur=self.conn.execute("""INSERT INTO workout_sets(session_id,exercise_id,set_number,reps,weight)
                VALUES(?,?,?,?,?)""",(session_id,exercise_id,set_number,reps,weight))
        return int(cur.lastrowid)

    def complete_session(self, session_id:int):
        with self.conn:
            self.conn.execute("UPDATE workout_sessions SET completed_at=CURRENT_TIMESTAMP WHERE id=?",(session_id,))

    def progress(self, exercise_id:int|None=None, limit:int=100):
        clause=""; params=[]
        if exercise_id is not None: clause="WHERE ws.exercise_id=?"; params.append(exercise_id)
        params.append(limit)
        return self.conn.execute(f"""SELECT ws.id,ws.exercise_id,e.exercise_name,ws.reps,ws.weight,
            ROUND(ws.reps*ws.weight,2) volume,
            ROUND(CASE WHEN ws.weight>0 THEN ws.weight*(1+ws.reps/30.0) ELSE 0 END,1) est_1rm,
            ws.completed_at,s.workout_name
            FROM workout_sets ws JOIN exercises e ON e.id=ws.exercise_id
            JOIN workout_sessions s ON s.id=ws.session_id {clause}
            ORDER BY ws.completed_at DESC,ws.id DESC LIMIT ?""",params).fetchall()

    def health(self)->dict:
        import time
        start=time.perf_counter(); self.conn.execute("SELECT 1").fetchone()
        return {"database":"HEALTHY","latency_ms":round((time.perf_counter()-start)*1000,2),
          "db_size_bytes":self.db_path.stat().st_size if self.db_path.exists() else 0,
          "exercises":self.count(),
          "workouts":self.conn.execute("SELECT COUNT(*) FROM workouts").fetchone()[0],
          "sessions":self.conn.execute("SELECT COUNT(*) FROM workout_sessions WHERE completed_at IS NOT NULL").fetchone()[0],
          "sets":self.conn.execute("SELECT COUNT(*) FROM workout_sets").fetchone()[0]}

    def stats(self) -> dict:
        q = self.conn.execute
        return {
            "exercises": self.count(),
            "names": q("SELECT COUNT(DISTINCT exercise_name) FROM exercises").fetchone()[0],
            "equipment": q("SELECT COUNT(DISTINCT equipment) FROM exercises").fetchone()[0],
            "muscles": q("SELECT COUNT(DISTINCT main_muscle) FROM exercises").fetchone()[0],
            "favorites": q("SELECT COUNT(*) FROM favorites").fetchone()[0],
            "avg_difficulty": q("SELECT ROUND(AVG(difficulty),2) FROM exercises").fetchone()[0],
            "by_muscle": q("SELECT main_muscle, COUNT(*) n FROM exercises GROUP BY main_muscle ORDER BY n DESC").fetchall(),
            "by_equipment": q("SELECT equipment, COUNT(*) n FROM exercises GROUP BY equipment ORDER BY n DESC LIMIT 10").fetchall(),
            "by_difficulty": q("SELECT difficulty, COUNT(*) n FROM exercises GROUP BY difficulty ORDER BY difficulty").fetchall(),
        }

    def export_rows(self, rows: Iterable[Exercise], path: Path) -> int:
        rows = list(rows)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", *CSV_COLUMNS, "favorite"])
            for e in rows:
                writer.writerow([e.id] + [getattr(e, c) for c in DB_COLUMNS] + [e.favorite])
        return len(rows)
