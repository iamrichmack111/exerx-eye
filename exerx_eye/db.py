from __future__ import annotations

import csv
import sqlite3
import secrets
from dataclasses import dataclass
from datetime import date, timedelta
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
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL COLLATE NOCASE UNIQUE,
            email TEXT NOT NULL COLLATE NOCASE UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS user_favorites (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id, exercise_id)
        );
        CREATE TABLE IF NOT EXISTS user_workouts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS user_workout_exercises (
            id INTEGER PRIMARY KEY,
            workout_id INTEGER NOT NULL REFERENCES user_workouts(id) ON DELETE CASCADE,
            exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
            position INTEGER NOT NULL DEFAULT 0, sets INTEGER NOT NULL DEFAULT 3,
            reps INTEGER NOT NULL DEFAULT 10, target_weight REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS user_workout_sessions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            workout_id INTEGER REFERENCES user_workouts(id) ON DELETE SET NULL,
            workout_name TEXT NOT NULL,
            started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS user_workout_sets (
            id INTEGER PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES user_workout_sessions(id) ON DELETE CASCADE,
            exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
            set_number INTEGER NOT NULL, reps INTEGER NOT NULL, weight REAL NOT NULL DEFAULT 0,
            completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            weekly_goal INTEGER NOT NULL DEFAULT 3 CHECK(weekly_goal BETWEEN 1 AND 7),
            default_rest INTEGER NOT NULL DEFAULT 60 CHECK(default_rest BETWEEN 15 AND 600),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS user_workout_schedule (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            weekday INTEGER NOT NULL CHECK(weekday BETWEEN 0 AND 6),
            workout_id INTEGER NOT NULL REFERENCES user_workouts(id) ON DELETE CASCADE,
            PRIMARY KEY(user_id, weekday)
        );
        CREATE INDEX IF NOT EXISTS idx_workout_exercises_workout ON workout_exercises(workout_id, position);
        CREATE INDEX IF NOT EXISTS idx_workout_sets_exercise ON workout_sets(exercise_id);
        CREATE INDEX IF NOT EXISTS idx_exercises_name ON exercises(exercise_name);
        CREATE INDEX IF NOT EXISTS idx_exercises_equipment ON exercises(equipment);
        CREATE INDEX IF NOT EXISTS idx_exercises_main_muscle ON exercises(main_muscle);
        CREATE INDEX IF NOT EXISTS idx_exercises_difficulty ON exercises(difficulty);
        CREATE INDEX IF NOT EXISTS idx_user_workouts_user ON user_workouts(user_id, id);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_workout_sessions(user_id, id);
        CREATE INDEX IF NOT EXISTS idx_user_sets_exercise ON user_workout_sets(exercise_id);
        CREATE INDEX IF NOT EXISTS idx_user_schedule_workout ON user_workout_schedule(workout_id);
        """)
        self.conn.execute("INSERT OR IGNORE INTO schema_migrations(version,name) VALUES(1,'base_exercise_schema')")
        self.conn.execute("INSERT OR IGNORE INTO schema_migrations(version,name) VALUES(2,'workout_tracking')")
        self.conn.execute("INSERT OR IGNORE INTO schema_migrations(version,name) VALUES(3,'analytics_and_health')")
        # Lightweight in-place migrations for existing SQLite databases.
        set_columns = {row[1] for row in self.conn.execute("PRAGMA table_info(user_workout_sets)").fetchall()}
        if "rir" not in set_columns:
            self.conn.execute("ALTER TABLE user_workout_sets ADD COLUMN rir INTEGER")
        if "note" not in set_columns:
            self.conn.execute("ALTER TABLE user_workout_sets ADD COLUMN note TEXT NOT NULL DEFAULT ''")
        session_columns = {row[1] for row in self.conn.execute("PRAGMA table_info(user_workout_sessions)").fetchall()}
        if "session_rpe" not in session_columns:
            self.conn.execute("ALTER TABLE user_workout_sessions ADD COLUMN session_rpe INTEGER")
        if "note" not in session_columns:
            self.conn.execute("ALTER TABLE user_workout_sessions ADD COLUMN note TEXT NOT NULL DEFAULT ''")
        self.conn.execute("INSERT OR IGNORE INTO schema_migrations(version,name) VALUES(4,'user_accounts_and_private_training_data')")
        self.conn.execute("INSERT OR IGNORE INTO schema_migrations(version,name) VALUES(5,'training_effort_dashboard_and_plan_editing')")
        self.conn.execute("INSERT OR IGNORE INTO schema_migrations(version,name) VALUES(6,'weekly_planning_preferences_and_session_review')")
        self.conn.execute("INSERT OR IGNORE INTO schema_migrations(version,name) VALUES(7,'username_only_auth_and_dark_mode')")
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
              limit: int = 500, user_id: int | None = None) -> list[Exercise]:
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
        if user_id is None:
            join = "LEFT JOIN favorites f ON f.exercise_id=e.id"
            join_params: list[object] = []
        else:
            join = "LEFT JOIN user_favorites f ON f.exercise_id=e.id AND f.user_id=?"
            join_params = [user_id]
        sql = f"""
          SELECT e.*, CASE WHEN f.exercise_id IS NULL THEN 0 ELSE 1 END AS favorite
          FROM exercises e {join}
          {where} ORDER BY e.main_muscle, e.exercise_name, e.equipment LIMIT ?
        """
        params.append(limit)
        return [Exercise(**dict(r)) for r in self.conn.execute(sql, [*join_params, *params]).fetchall()]

    def get(self, exercise_id: int, user_id: int | None = None) -> Exercise | None:
        if user_id is None:
            row = self.conn.execute("""
              SELECT e.*, CASE WHEN f.exercise_id IS NULL THEN 0 ELSE 1 END AS favorite
              FROM exercises e LEFT JOIN favorites f ON f.exercise_id=e.id WHERE e.id=?
            """, (exercise_id,)).fetchone()
        else:
            row = self.conn.execute("""
              SELECT e.*, CASE WHEN f.exercise_id IS NULL THEN 0 ELSE 1 END AS favorite
              FROM exercises e LEFT JOIN user_favorites f ON f.exercise_id=e.id AND f.user_id=?
              WHERE e.id=?
            """, (user_id, exercise_id)).fetchone()
        return Exercise(**dict(row)) if row else None

    def distinct(self, column: str) -> list[str]:
        if column not in {"equipment", "main_muscle", "target_muscles", "utility", "mechanics", "force"}:
            raise ValueError("Unsupported distinct column")
        rows = self.conn.execute(
            f"SELECT DISTINCT {column} FROM exercises WHERE {column} <> '' ORDER BY {column} COLLATE NOCASE"
        ).fetchall()
        return [r[0] for r in rows]

    def random(self, muscle: str | None = None, count: int = 1, user_id: int | None = None) -> list[Exercise]:
        where, params = "", []
        if muscle and muscle != "All":
            where = "WHERE LOWER(e.target_muscles) LIKE ? OR e.main_muscle = ?"
            params = [f"%{muscle.lower()}%", muscle]
        if user_id is None:
            join = "LEFT JOIN favorites f ON f.exercise_id=e.id"
            join_params: list[object] = []
        else:
            join = "LEFT JOIN user_favorites f ON f.exercise_id=e.id AND f.user_id=?"
            join_params = [user_id]
        params.append(count)
        rows = self.conn.execute(f"""
          SELECT e.*, CASE WHEN f.exercise_id IS NULL THEN 0 ELSE 1 END AS favorite
          FROM exercises e {join}
          {where} ORDER BY RANDOM() LIMIT ?
        """, [*join_params, *params]).fetchall()
        return [Exercise(**dict(r)) for r in rows]

    def random_per_main_muscle(self, count_each: int = 1, user_id: int | None = None) -> list[Exercise]:
        result: list[Exercise] = []
        for muscle in self.distinct("main_muscle"):
            result.extend(self.random(muscle, count_each, user_id=user_id))
        return result

    def toggle_favorite(self, exercise_id: int, user_id: int | None = None) -> bool:
        if user_id is None:
            exists = self.conn.execute("SELECT 1 FROM favorites WHERE exercise_id=?", (exercise_id,)).fetchone()
            with self.conn:
                if exists:
                    self.conn.execute("DELETE FROM favorites WHERE exercise_id=?", (exercise_id,))
                    return False
                self.conn.execute("INSERT INTO favorites(exercise_id) VALUES(?)", (exercise_id,))
                return True
        exists = self.conn.execute(
            "SELECT 1 FROM user_favorites WHERE user_id=? AND exercise_id=?",
            (user_id, exercise_id),
        ).fetchone()
        with self.conn:
            if exists:
                self.conn.execute(
                    "DELETE FROM user_favorites WHERE user_id=? AND exercise_id=?",
                    (user_id, exercise_id),
                )
                return False
            self.conn.execute(
                "INSERT INTO user_favorites(user_id,exercise_id) VALUES(?,?)",
                (user_id, exercise_id),
            )
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

    def remove_from_workout(self, workout_id: int, item_id: int) -> bool:
        with self.conn:
            cur = self.conn.execute(
                "DELETE FROM workout_exercises WHERE id=? AND workout_id=?",
                (item_id, workout_id),
            )
        return cur.rowcount > 0

    def duplicate_workout(self, workout_id: int) -> int:
        source = self.conn.execute(
            "SELECT name, notes FROM workouts WHERE id=?", (workout_id,)
        ).fetchone()
        if source is None:
            raise ValueError("Workout not found")
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO workouts(name,notes) VALUES(?,?)",
                (f"{source['name']} copy", source['notes']),
            )
            new_id = int(cur.lastrowid)
            self.conn.execute(
                """INSERT INTO workout_exercises(workout_id,exercise_id,position,sets,reps,target_weight)
                   SELECT ?,exercise_id,position,sets,reps,target_weight
                   FROM workout_exercises WHERE workout_id=? ORDER BY position,id""",
                (new_id, workout_id),
            )
        return new_id

    def delete_workout(self, workout_id: int) -> bool:
        with self.conn:
            cur = self.conn.execute("DELETE FROM workouts WHERE id=?", (workout_id,))
        return cur.rowcount > 0

    def session_summary(self, workout_id: int, session_id: int | None = None) -> dict:
        planned_sets = int(self.conn.execute(
            "SELECT COALESCE(SUM(sets),0) FROM workout_exercises WHERE workout_id=?",
            (workout_id,),
        ).fetchone()[0])
        logged_sets = 0
        volume = 0.0
        started_at = None
        if session_id:
            session = self.conn.execute(
                "SELECT started_at FROM workout_sessions WHERE id=? AND workout_id=?",
                (session_id, workout_id),
            ).fetchone()
            if session:
                started_at = session['started_at']
                row = self.conn.execute(
                    "SELECT COUNT(*) n, COALESCE(SUM(reps*weight),0) volume FROM workout_sets WHERE session_id=?",
                    (session_id,),
                ).fetchone()
                logged_sets = int(row['n'])
                volume = float(row['volume'])
        percent = min(100, round((logged_sets / planned_sets * 100) if planned_sets else 0))
        return {
            "planned_sets": planned_sets,
            "logged_sets": logged_sets,
            "remaining_sets": max(0, planned_sets - logged_sets),
            "percent": percent,
            "volume": round(volume, 1),
            "started_at": started_at,
        }

    def exercise_best(self, exercise_id: int) -> dict:
        row = self.conn.execute(
            """SELECT COUNT(*) sets, COUNT(DISTINCT session_id) sessions,
                      COALESCE(MAX(weight),0) max_weight,
                      COALESCE(MAX(CASE WHEN weight>0 THEN weight*(1+reps/30.0) ELSE 0 END),0) best_1rm,
                      COALESCE(SUM(reps*weight),0) volume
               FROM workout_sets WHERE exercise_id=?""",
            (exercise_id,),
        ).fetchone()
        return {
            "sets": int(row['sets']),
            "sessions": int(row['sessions']),
            "max_weight": round(float(row['max_weight']), 1),
            "best_1rm": round(float(row['best_1rm']), 1),
            "volume": round(float(row['volume']), 1),
        }

    def progress_summary(self, exercise_id: int | None = None) -> dict:
        clause = "WHERE ws.exercise_id=?" if exercise_id is not None else ""
        params = (exercise_id,) if exercise_id is not None else ()
        row = self.conn.execute(
            f"""SELECT COUNT(*) sets, COUNT(DISTINCT ws.session_id) sessions,
                       COALESCE(SUM(ws.reps*ws.weight),0) volume,
                       COALESCE(MAX(ws.weight),0) max_weight,
                       COALESCE(MAX(CASE WHEN ws.weight>0 THEN ws.weight*(1+ws.reps/30.0) ELSE 0 END),0) best_1rm
                FROM workout_sets ws {clause}""",
            params,
        ).fetchone()
        return {
            "sets": int(row['sets']),
            "sessions": int(row['sessions']),
            "volume": round(float(row['volume']), 1),
            "max_weight": round(float(row['max_weight']), 1),
            "best_1rm": round(float(row['best_1rm']), 1),
        }

    def health(self)->dict:
        import time
        start=time.perf_counter(); self.conn.execute("SELECT 1").fetchone()
        return {"database":"HEALTHY","latency_ms":round((time.perf_counter()-start)*1000,2),
          "db_size_bytes":self.db_path.stat().st_size if self.db_path.exists() else 0,
          "exercises":self.count(),
          "workouts":self.conn.execute("SELECT COUNT(*) FROM workouts").fetchone()[0],
          "sessions":self.conn.execute("SELECT COUNT(*) FROM workout_sessions WHERE completed_at IS NOT NULL").fetchone()[0],
          "sets":self.conn.execute("SELECT COUNT(*) FROM workout_sets").fetchone()[0]}

    def stats(self, user_id: int | None = None) -> dict:
        q = self.conn.execute
        favorites_count = (
            q("SELECT COUNT(*) FROM favorites").fetchone()[0]
            if user_id is None
            else q("SELECT COUNT(*) FROM user_favorites WHERE user_id=?", (user_id,)).fetchone()[0]
        )
        return {
            "exercises": self.count(),
            "names": q("SELECT COUNT(DISTINCT exercise_name) FROM exercises").fetchone()[0],
            "equipment": q("SELECT COUNT(DISTINCT equipment) FROM exercises").fetchone()[0],
            "muscles": q("SELECT COUNT(DISTINCT main_muscle) FROM exercises").fetchone()[0],
            "favorites": favorites_count,
            "avg_difficulty": q("SELECT ROUND(AVG(difficulty),2) FROM exercises").fetchone()[0],
            "by_muscle": q("SELECT main_muscle, COUNT(*) n FROM exercises GROUP BY main_muscle ORDER BY n DESC").fetchall(),
            "by_equipment": q("SELECT equipment, COUNT(*) n FROM exercises GROUP BY equipment ORDER BY n DESC LIMIT 10").fetchall(),
            "by_difficulty": q("SELECT difficulty, COUNT(*) n FROM exercises GROUP BY difficulty ORDER BY difficulty").fetchall(),
        }

    def create_user(self, username: str, password_or_email: str, password_hash: str | None = None) -> int:
        """Create a local account.

        New code uses create_user(username, password_hash). The 3-argument form is
        retained for database/API compatibility with older ExerxEye builds, but
        email is no longer part of the product's sign-up or login experience.
        """
        username = username.strip()
        if password_hash is None:
            password_hash = password_or_email
            email = f"local-{secrets.token_hex(12)}@exerxeye.invalid"
        else:
            email = password_or_email.strip().lower() or f"local-{secrets.token_hex(12)}@exerxeye.invalid"
        if not username or not password_hash:
            raise ValueError("Username and password are required")
        try:
            with self.conn:
                cur = self.conn.execute(
                    "INSERT INTO users(username,email,password_hash) VALUES(?,?,?)",
                    (username, email, password_hash),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("That username is already registered") from exc
        return int(cur.lastrowid)

    def user_by_id(self, user_id: int):
        return self.conn.execute(
            "SELECT id,username,email,password_hash,created_at FROM users WHERE id=?",
            (user_id,),
        ).fetchone()

    def user_by_login(self, login: str):
        value = login.strip().lower()
        return self.conn.execute(
            "SELECT id,username,email,password_hash,created_at FROM users WHERE LOWER(username)=?",
            (value,),
        ).fetchone()

    def user_preferences(self, user_id: int) -> dict:
        row = self.conn.execute(
            "SELECT weekly_goal,default_rest FROM user_preferences WHERE user_id=?",
            (user_id,),
        ).fetchone()
        if row is None:
            with self.conn:
                self.conn.execute(
                    "INSERT OR IGNORE INTO user_preferences(user_id) VALUES(?)",
                    (user_id,),
                )
            row = self.conn.execute(
                "SELECT weekly_goal,default_rest FROM user_preferences WHERE user_id=?",
                (user_id,),
            ).fetchone()
        return {"weekly_goal": int(row["weekly_goal"]), "default_rest": int(row["default_rest"])}

    def update_user_preferences(self, user_id: int, weekly_goal: int, default_rest: int) -> dict:
        weekly_goal = max(1, min(int(weekly_goal), 7))
        default_rest = max(15, min(int(default_rest), 600))
        with self.conn:
            self.conn.execute(
                """INSERT INTO user_preferences(user_id,weekly_goal,default_rest,updated_at)
                   VALUES(?,?,?,CURRENT_TIMESTAMP)
                   ON CONFLICT(user_id) DO UPDATE SET
                     weekly_goal=excluded.weekly_goal,
                     default_rest=excluded.default_rest,
                     updated_at=CURRENT_TIMESTAMP""",
                (user_id, weekly_goal, default_rest),
            )
        return self.user_preferences(user_id)

    def user_schedule(self, user_id: int):
        return self.conn.execute(
            """SELECT sc.weekday,sc.workout_id,w.name,w.notes,COUNT(we.id) exercise_count
               FROM user_workout_schedule sc
               JOIN user_workouts w ON w.id=sc.workout_id AND w.user_id=sc.user_id
               LEFT JOIN user_workout_exercises we ON we.workout_id=w.id
               WHERE sc.user_id=?
               GROUP BY sc.weekday,sc.workout_id,w.name,w.notes
               ORDER BY sc.weekday""",
            (user_id,),
        ).fetchall()

    def set_user_schedule(self, user_id: int, weekday: int, workout_id: int | None) -> bool:
        weekday = int(weekday)
        if weekday < 0 or weekday > 6:
            return False
        if workout_id is None:
            with self.conn:
                self.conn.execute(
                    "DELETE FROM user_workout_schedule WHERE user_id=? AND weekday=?",
                    (user_id, weekday),
                )
            return True
        if self.user_workout(user_id, int(workout_id)) is None:
            return False
        with self.conn:
            self.conn.execute(
                """INSERT INTO user_workout_schedule(user_id,weekday,workout_id) VALUES(?,?,?)
                   ON CONFLICT(user_id,weekday) DO UPDATE SET workout_id=excluded.workout_id""",
                (user_id, weekday, int(workout_id)),
            )
        return True

    def user_active_session(self, user_id: int):
        return self.conn.execute(
            """SELECT s.id,s.workout_id,s.workout_name,s.started_at,COUNT(ws.id) logged_sets
               FROM user_workout_sessions s
               LEFT JOIN user_workout_sets ws ON ws.session_id=s.id
               WHERE s.user_id=? AND s.completed_at IS NULL
               GROUP BY s.id ORDER BY s.id DESC LIMIT 1""",
            (user_id,),
        ).fetchone()

    def user_week_goal(self, user_id: int) -> dict:
        prefs = self.user_preferences(user_id)
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        row = self.conn.execute(
            """SELECT COUNT(*) sessions FROM user_workout_sessions
               WHERE user_id=? AND completed_at IS NOT NULL AND datetime(completed_at) >= datetime(?)""",
            (user_id, f"{week_start.isoformat()} 00:00:00"),
        ).fetchone()
        sessions = int(row["sessions"])
        goal = prefs["weekly_goal"]
        return {
            "sessions": sessions,
            "goal": goal,
            "remaining": max(0, goal - sessions),
            "percent": min(100, round((sessions / goal * 100) if goal else 0)),
        }

    def create_user_workout(self, user_id: int, name: str, notes: str = "") -> int:
        name = name.strip()
        if not name:
            raise ValueError("Workout name is required")
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO user_workouts(user_id,name,notes) VALUES(?,?,?)",
                (user_id, name, notes.strip()),
            )
        return int(cur.lastrowid)

    def list_user_workouts(self, user_id: int):
        return self.conn.execute(
            """SELECT w.id,w.name,w.notes,w.created_at,COUNT(we.id) exercise_count
               FROM user_workouts w LEFT JOIN user_workout_exercises we ON we.workout_id=w.id
               WHERE w.user_id=? GROUP BY w.id ORDER BY w.id DESC""",
            (user_id,),
        ).fetchall()

    def user_workout(self, user_id: int, workout_id: int):
        return self.conn.execute(
            "SELECT * FROM user_workouts WHERE id=? AND user_id=?",
            (workout_id, user_id),
        ).fetchone()

    def add_to_user_workout(self, user_id: int, workout_id: int, exercise_id: int, sets: int = 3, reps: int = 10, target_weight: float = 0):
        if self.user_workout(user_id, workout_id) is None:
            raise ValueError("Workout not found")
        pos = self.conn.execute(
            "SELECT COALESCE(MAX(position),0)+1 FROM user_workout_exercises WHERE workout_id=?",
            (workout_id,),
        ).fetchone()[0]
        with self.conn:
            self.conn.execute(
                """INSERT INTO user_workout_exercises
                   (workout_id,exercise_id,position,sets,reps,target_weight) VALUES(?,?,?,?,?,?)""",
                (workout_id, exercise_id, pos, sets, reps, target_weight),
            )

    def user_workout_detail(self, user_id: int, workout_id: int):
        if self.user_workout(user_id, workout_id) is None:
            return []
        return self.conn.execute(
            """SELECT we.id item_id,we.position,we.sets,we.reps,we.target_weight,
                      e.id exercise_id,e.exercise_name,e.main_muscle,e.equipment
               FROM user_workout_exercises we JOIN exercises e ON e.id=we.exercise_id
               WHERE we.workout_id=? ORDER BY we.position,we.id""",
            (workout_id,),
        ).fetchall()

    def duplicate_user_workout(self, user_id: int, workout_id: int) -> int:
        source = self.user_workout(user_id, workout_id)
        if source is None:
            raise ValueError("Workout not found")
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO user_workouts(user_id,name,notes) VALUES(?,?,?)",
                (user_id, f"{source['name']} copy", source['notes']),
            )
            new_id = int(cur.lastrowid)
            self.conn.execute(
                """INSERT INTO user_workout_exercises(workout_id,exercise_id,position,sets,reps,target_weight)
                   SELECT ?,exercise_id,position,sets,reps,target_weight
                   FROM user_workout_exercises WHERE workout_id=? ORDER BY position,id""",
                (new_id, workout_id),
            )
        return new_id

    def delete_user_workout(self, user_id: int, workout_id: int) -> bool:
        with self.conn:
            cur = self.conn.execute(
                "DELETE FROM user_workouts WHERE id=? AND user_id=?",
                (workout_id, user_id),
            )
        return cur.rowcount > 0

    def remove_from_user_workout(self, user_id: int, workout_id: int, item_id: int) -> bool:
        if self.user_workout(user_id, workout_id) is None:
            return False
        with self.conn:
            cur = self.conn.execute(
                "DELETE FROM user_workout_exercises WHERE id=? AND workout_id=?",
                (item_id, workout_id),
            )
        return cur.rowcount > 0

    def start_user_session(self, user_id: int, workout_id: int) -> int:
        workout = self.user_workout(user_id, workout_id)
        if workout is None:
            raise ValueError("Workout not found")
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO user_workout_sessions(user_id,workout_id,workout_name) VALUES(?,?,?)",
                (user_id, workout_id, workout['name']),
            )
        return int(cur.lastrowid)

    def user_session(self, user_id: int, session_id: int):
        return self.conn.execute(
            "SELECT * FROM user_workout_sessions WHERE id=? AND user_id=?",
            (session_id, user_id),
        ).fetchone()

    def discard_user_session(self, user_id: int, session_id: int) -> bool:
        with self.conn:
            cur = self.conn.execute(
                "DELETE FROM user_workout_sessions WHERE id=? AND user_id=? AND completed_at IS NULL",
                (session_id, user_id),
            )
        return cur.rowcount > 0

    def user_session_set_count(self, user_id: int, session_id: int, exercise_id: int) -> int:
        if self.user_session(user_id, session_id) is None:
            return 0
        return int(self.conn.execute(
            "SELECT COUNT(*) FROM user_workout_sets WHERE session_id=? AND exercise_id=?",
            (session_id, exercise_id),
        ).fetchone()[0])

    def log_user_set(self, user_id: int, session_id: int, exercise_id: int, set_number: int, reps: int, weight: float = 0, rir: int | None = None, note: str = "") -> int:
        session = self.user_session(user_id, session_id)
        if session is None:
            raise ValueError("Session not found")
        if rir is not None:
            rir = max(0, min(int(rir), 10))
        with self.conn:
            cur = self.conn.execute(
                """INSERT INTO user_workout_sets(session_id,exercise_id,set_number,reps,weight,rir,note)
                   VALUES(?,?,?,?,?,?,?)""",
                (session_id, exercise_id, set_number, reps, weight, rir, note.strip()[:240]),
            )
        return int(cur.lastrowid)

    def complete_user_session(self, user_id: int, session_id: int) -> bool:
        with self.conn:
            cur = self.conn.execute(
                "UPDATE user_workout_sessions SET completed_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",
                (session_id, user_id),
            )
        return cur.rowcount > 0

    def update_user_session_review(self, user_id: int, session_id: int, session_rpe: int | None, note: str = "") -> bool:
        if session_rpe is not None:
            session_rpe = max(1, min(int(session_rpe), 10))
        with self.conn:
            cur = self.conn.execute(
                """UPDATE user_workout_sessions SET session_rpe=?, note=?
                   WHERE id=? AND user_id=?""",
                (session_rpe, note.strip()[:500], session_id, user_id),
            )
        return cur.rowcount > 0

    def user_session_review(self, user_id: int, session_id: int) -> dict | None:
        session = self.user_session(user_id, session_id)
        if session is None:
            return None
        totals = self.conn.execute(
            """SELECT COUNT(*) sets,COUNT(DISTINCT exercise_id) exercises,
                      ROUND(COALESCE(SUM(reps*weight),0),1) volume,
                      ROUND(AVG(rir),1) avg_rir,
                      ROUND(MAX(CASE WHEN weight>0 THEN weight*(1+reps/30.0) ELSE 0 END),1) top_1rm
               FROM user_workout_sets WHERE session_id=?""",
            (session_id,),
        ).fetchone()
        duration = self.conn.execute(
            """SELECT CASE WHEN completed_at IS NOT NULL THEN
                        ROUND((julianday(completed_at)-julianday(started_at))*1440)
                      ELSE ROUND((julianday('now')-julianday(started_at))*1440) END minutes
               FROM user_workout_sessions WHERE id=?""",
            (session_id,),
        ).fetchone()[0]
        exercises = self.conn.execute(
            """SELECT e.id exercise_id,e.exercise_name,COUNT(ws.id) sets,
                      SUM(ws.reps) reps,ROUND(SUM(ws.reps*ws.weight),1) volume,
                      ROUND(MAX(ws.weight),1) max_weight,ROUND(AVG(ws.rir),1) avg_rir
               FROM user_workout_sets ws JOIN exercises e ON e.id=ws.exercise_id
               WHERE ws.session_id=? GROUP BY e.id,e.exercise_name ORDER BY MIN(ws.id)""",
            (session_id,),
        ).fetchall()
        return {
            "session": session,
            "sets": int(totals["sets"]),
            "exercises": int(totals["exercises"]),
            "volume": float(totals["volume"] or 0),
            "avg_rir": totals["avg_rir"],
            "top_1rm": float(totals["top_1rm"] or 0),
            "duration_minutes": int(duration or 0),
            "exercise_rows": exercises,
        }

    def user_session_summary(self, user_id: int, workout_id: int, session_id: int | None = None) -> dict:
        if self.user_workout(user_id, workout_id) is None:
            return {"planned_sets":0,"logged_sets":0,"remaining_sets":0,"percent":0,"volume":0.0,"started_at":None}
        planned_sets = int(self.conn.execute(
            "SELECT COALESCE(SUM(sets),0) FROM user_workout_exercises WHERE workout_id=?",
            (workout_id,),
        ).fetchone()[0])
        logged_sets = 0
        volume = 0.0
        started_at = None
        if session_id:
            session = self.conn.execute(
                "SELECT started_at FROM user_workout_sessions WHERE id=? AND workout_id=? AND user_id=?",
                (session_id, workout_id, user_id),
            ).fetchone()
            if session:
                started_at = session['started_at']
                row = self.conn.execute(
                    "SELECT COUNT(*) n, COALESCE(SUM(reps*weight),0) volume FROM user_workout_sets WHERE session_id=?",
                    (session_id,),
                ).fetchone()
                logged_sets = int(row['n'])
                volume = float(row['volume'])
        percent = min(100, round((logged_sets / planned_sets * 100) if planned_sets else 0))
        return {
            "planned_sets": planned_sets,
            "logged_sets": logged_sets,
            "remaining_sets": max(0, planned_sets - logged_sets),
            "percent": percent,
            "volume": round(volume, 1),
            "started_at": started_at,
        }

    def user_progress(self, user_id: int, exercise_id: int | None = None, limit: int = 100, days: int | None = None):
        clauses = ["s.user_id=?"]
        params: list[object] = [user_id]
        if exercise_id is not None:
            clauses.append("ws.exercise_id=?")
            params.append(exercise_id)
        if days is not None:
            clauses.append("datetime(ws.completed_at) >= datetime('now', ?)")
            params.append(f'-{max(1, int(days))} days')
        params.append(limit)
        where = "WHERE " + " AND ".join(clauses)
        return self.conn.execute(
            f"""SELECT ws.id,ws.exercise_id,e.exercise_name,ws.reps,ws.weight,
                       ROUND(ws.reps*ws.weight,2) volume,
                       ROUND(CASE WHEN ws.weight>0 THEN ws.weight*(1+ws.reps/30.0) ELSE 0 END,1) est_1rm,
                       ws.rir,ws.note,ws.completed_at,s.workout_name
                FROM user_workout_sets ws JOIN exercises e ON e.id=ws.exercise_id
                JOIN user_workout_sessions s ON s.id=ws.session_id {where}
                ORDER BY ws.completed_at DESC,ws.id DESC LIMIT ?""",
            params,
        ).fetchall()

    def user_exercise_best(self, user_id: int, exercise_id: int) -> dict:
        row = self.conn.execute(
            """SELECT COUNT(*) sets, COUNT(DISTINCT ws.session_id) sessions,
                      COALESCE(MAX(ws.weight),0) max_weight,
                      COALESCE(MAX(CASE WHEN ws.weight>0 THEN ws.weight*(1+ws.reps/30.0) ELSE 0 END),0) best_1rm,
                      COALESCE(SUM(ws.reps*ws.weight),0) volume
               FROM user_workout_sets ws JOIN user_workout_sessions s ON s.id=ws.session_id
               WHERE s.user_id=? AND ws.exercise_id=?""",
            (user_id, exercise_id),
        ).fetchone()
        return {
            "sets": int(row['sets']),
            "sessions": int(row['sessions']),
            "max_weight": round(float(row['max_weight']), 1),
            "best_1rm": round(float(row['best_1rm']), 1),
            "volume": round(float(row['volume']), 1),
        }

    def user_progress_summary(self, user_id: int, exercise_id: int | None = None, days: int | None = None) -> dict:
        clauses = ["s.user_id=?"]
        params: list[object] = [user_id]
        if exercise_id is not None:
            clauses.append("ws.exercise_id=?")
            params.append(exercise_id)
        if days is not None:
            clauses.append("datetime(ws.completed_at) >= datetime('now', ?)")
            params.append(f'-{max(1, int(days))} days')
        where = "WHERE " + " AND ".join(clauses)
        row = self.conn.execute(
            f"""SELECT COUNT(*) sets, COUNT(DISTINCT ws.session_id) sessions,
                       COALESCE(SUM(ws.reps*ws.weight),0) volume,
                       COALESCE(MAX(ws.weight),0) max_weight,
                       COALESCE(MAX(CASE WHEN ws.weight>0 THEN ws.weight*(1+ws.reps/30.0) ELSE 0 END),0) best_1rm
                FROM user_workout_sets ws JOIN user_workout_sessions s ON s.id=ws.session_id {where}""",
            params,
        ).fetchone()
        return {
            "sets": int(row['sets']),
            "sessions": int(row['sessions']),
            "volume": round(float(row['volume']), 1),
            "max_weight": round(float(row['max_weight']), 1),
            "best_1rm": round(float(row['best_1rm']), 1),
        }


    def update_user_workout(self, user_id: int, workout_id: int, name: str, notes: str = "") -> bool:
        name = name.strip()
        if not name:
            raise ValueError("Workout name is required")
        with self.conn:
            cur = self.conn.execute(
                "UPDATE user_workouts SET name=?, notes=? WHERE id=? AND user_id=?",
                (name, notes.strip(), workout_id, user_id),
            )
        return cur.rowcount > 0

    def update_user_workout_item(self, user_id: int, workout_id: int, item_id: int, sets: int, reps: int, target_weight: float) -> bool:
        if self.user_workout(user_id, workout_id) is None:
            return False
        with self.conn:
            cur = self.conn.execute(
                """UPDATE user_workout_exercises
                   SET sets=?, reps=?, target_weight=?
                   WHERE id=? AND workout_id=?""",
                (max(1, sets), max(1, reps), max(0.0, target_weight), item_id, workout_id),
            )
        return cur.rowcount > 0

    def move_user_workout_item(self, user_id: int, workout_id: int, item_id: int, direction: str) -> bool:
        if self.user_workout(user_id, workout_id) is None:
            return False
        items = self.conn.execute(
            "SELECT id,position FROM user_workout_exercises WHERE workout_id=? ORDER BY position,id",
            (workout_id,),
        ).fetchall()
        ids = [int(row['id']) for row in items]
        if item_id not in ids:
            return False
        idx = ids.index(item_id)
        target = idx - 1 if direction == 'up' else idx + 1
        if target < 0 or target >= len(ids):
            return False
        ids[idx], ids[target] = ids[target], ids[idx]
        with self.conn:
            for position, row_id in enumerate(ids, 1):
                self.conn.execute(
                    "UPDATE user_workout_exercises SET position=? WHERE id=? AND workout_id=?",
                    (position, row_id, workout_id),
                )
        return True

    def user_session_sets(self, user_id: int, session_id: int):
        if self.user_session(user_id, session_id) is None:
            return []
        return self.conn.execute(
            """SELECT ws.*, e.exercise_name
               FROM user_workout_sets ws JOIN exercises e ON e.id=ws.exercise_id
               WHERE ws.session_id=? ORDER BY ws.id""",
            (session_id,),
        ).fetchall()

    def user_recent_sessions(self, user_id: int, limit: int = 6):
        return self.conn.execute(
            """SELECT s.id,s.workout_id,s.workout_name,s.started_at,s.completed_at,s.session_rpe,s.note,
                      COUNT(ws.id) set_count,
                      ROUND(COALESCE(SUM(ws.reps*ws.weight),0),1) volume
               FROM user_workout_sessions s
               LEFT JOIN user_workout_sets ws ON ws.session_id=s.id
               WHERE s.user_id=? AND s.completed_at IS NOT NULL
               GROUP BY s.id ORDER BY s.completed_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()

    def user_volume_trend(self, user_id: int, days: int = 30):
        return self.conn.execute(
            """SELECT date(ws.completed_at) day,
                      ROUND(COALESCE(SUM(ws.reps*ws.weight),0),1) volume,
                      COUNT(ws.id) sets
               FROM user_workout_sets ws
               JOIN user_workout_sessions s ON s.id=ws.session_id
               WHERE s.user_id=? AND datetime(ws.completed_at) >= datetime('now', ?)
               GROUP BY date(ws.completed_at) ORDER BY day""",
            (user_id, f'-{max(1, int(days))} days'),
        ).fetchall()

    def user_recent_prs(self, user_id: int, limit: int = 6):
        return self.conn.execute(
            """WITH scored AS (
                 SELECT ws.id,ws.exercise_id,e.exercise_name,ws.reps,ws.weight,ws.completed_at,
                        CASE WHEN ws.weight>0 THEN ws.weight*(1+ws.reps/30.0) ELSE 0 END est_1rm
                 FROM user_workout_sets ws
                 JOIN user_workout_sessions s ON s.id=ws.session_id
                 JOIN exercises e ON e.id=ws.exercise_id
                 WHERE s.user_id=?
               )
               SELECT ROUND(a.est_1rm,1) est_1rm,a.exercise_id,a.exercise_name,a.reps,a.weight,a.completed_at
               FROM scored a
               WHERE a.est_1rm > 0
                 AND a.est_1rm >= (SELECT MAX(b.est_1rm) FROM scored b WHERE b.exercise_id=a.exercise_id)
               ORDER BY a.completed_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()

    def user_training_streak(self, user_id: int) -> dict:
        rows = self.conn.execute(
            """SELECT DISTINCT date(completed_at) day
               FROM user_workout_sessions
               WHERE user_id=? AND completed_at IS NOT NULL
               ORDER BY day DESC""",
            (user_id,),
        ).fetchall()
        trained = {date.fromisoformat(row["day"]) for row in rows if row["day"]}
        if not trained:
            return {"current": 0, "best": 0}

        today = date.today()
        cursor = today if today in trained else today - timedelta(days=1)
        current = 0
        while cursor in trained:
            current += 1
            cursor -= timedelta(days=1)

        best = 0
        running = 0
        previous = None
        for day in sorted(trained):
            if previous is not None and day == previous + timedelta(days=1):
                running += 1
            else:
                running = 1
            best = max(best, running)
            previous = day
        return {"current": current, "best": best}

    def user_week_activity(self, user_id: int) -> list[dict]:
        start = date.today() - timedelta(days=date.today().weekday())
        rows = self.conn.execute(
            """SELECT date(completed_at) day, COUNT(*) sessions
               FROM user_workout_sessions
               WHERE user_id=? AND completed_at IS NOT NULL AND date(completed_at) >= ?
               GROUP BY date(completed_at)""",
            (user_id, start.isoformat()),
        ).fetchall()
        counts = {row["day"]: int(row["sessions"]) for row in rows}
        return [
            {"day": (start + timedelta(days=i)).isoformat(), "weekday": i, "sessions": counts.get((start + timedelta(days=i)).isoformat(), 0)}
            for i in range(7)
        ]

    def user_muscle_volume(self, user_id: int, days: int = 30, limit: int = 6):
        return self.conn.execute(
            """SELECT COALESCE(NULLIF(e.main_muscle,''),'Other') muscle,
                      COUNT(ws.id) sets,
                      ROUND(COALESCE(SUM(ws.reps*ws.weight),0),1) volume
               FROM user_workout_sets ws
               JOIN user_workout_sessions s ON s.id=ws.session_id
               JOIN exercises e ON e.id=ws.exercise_id
               WHERE s.user_id=? AND datetime(ws.completed_at) >= datetime('now', ?)
               GROUP BY COALESCE(NULLIF(e.main_muscle,''),'Other')
               ORDER BY volume DESC, sets DESC LIMIT ?""",
            (user_id, f'-{max(1, int(days))} days', max(1, int(limit))),
        ).fetchall()

    def user_dashboard(self, user_id: int) -> dict:
        summary = self.user_progress_summary(user_id)
        week = self.conn.execute(
            """SELECT COUNT(DISTINCT s.id) sessions, COUNT(ws.id) sets,
                      ROUND(COALESCE(SUM(ws.reps*ws.weight),0),1) volume
               FROM user_workout_sessions s
               LEFT JOIN user_workout_sets ws ON ws.session_id=s.id
               WHERE s.user_id=? AND s.completed_at IS NOT NULL
                 AND datetime(s.completed_at) >= datetime('now','-7 days')""",
            (user_id,),
        ).fetchone()
        active_days = int(self.conn.execute(
            """SELECT COUNT(DISTINCT date(completed_at)) FROM user_workout_sessions
               WHERE user_id=? AND completed_at IS NOT NULL
                 AND datetime(completed_at) >= datetime('now','-30 days')""",
            (user_id,),
        ).fetchone()[0])
        last_workout = self.conn.execute(
            """SELECT w.id,w.name,w.notes,COUNT(we.id) exercise_count
               FROM user_workouts w LEFT JOIN user_workout_exercises we ON we.workout_id=w.id
               WHERE w.user_id=?
               GROUP BY w.id ORDER BY w.id DESC LIMIT 1""",
            (user_id,),
        ).fetchone()
        return {
            'summary': summary,
            'week': {'sessions': int(week['sessions']), 'sets': int(week['sets']), 'volume': float(week['volume'])},
            'active_days_30': active_days,
            'last_workout': last_workout,
            'recent_sessions': self.user_recent_sessions(user_id, 5),
            'recent_prs': self.user_recent_prs(user_id, 5),
            'trend': self.user_volume_trend(user_id, 30),
            'active_session': self.user_active_session(user_id),
            'week_goal': self.user_week_goal(user_id),
            'schedule': self.user_schedule(user_id),
            'preferences': self.user_preferences(user_id),
            'streak': self.user_training_streak(user_id),
            'week_activity': self.user_week_activity(user_id),
            'muscle_volume': self.user_muscle_volume(user_id, 30, 6),
        }

    def user_export_bundle(self, user_id: int) -> dict:
        user = self.user_by_id(user_id)
        favorites = self.query(favorites_only=True, limit=5000, user_id=user_id)
        workouts = []
        for workout in self.list_user_workouts(user_id):
            workouts.append({
                "id": workout['id'],
                "name": workout['name'],
                "notes": workout['notes'],
                "created_at": workout['created_at'],
                "exercises": [dict(row) for row in self.user_workout_detail(user_id, workout['id'])],
            })
        return {
            "account": {
                "username": user['username'] if user else '',
                "created_at": user['created_at'] if user else '',
            },
            "favorites": [
                {"id": e.id, "name": e.exercise_name, "muscle": e.main_muscle, "equipment": e.equipment}
                for e in favorites
            ],
            "workouts": workouts,
            "progress": [dict(row) for row in self.user_progress(user_id, limit=10000)],
            "preferences": self.user_preferences(user_id),
            "schedule": [dict(row) for row in self.user_schedule(user_id)],
            "sessions": [dict(row) for row in self.user_recent_sessions(user_id, 10000)],
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
