from __future__ import annotations

import csv
import io
import json
import os
import random
from dataclasses import asdict
from datetime import date, timedelta
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse

from flask import (
    Flask,
    Response,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from exerx_eye.db import ExerxEye, SEARCHABLE

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "instance" / "exercises.db"
DEFAULT_CSV_PATH = BASE_DIR / "data" / "gym_exercise_dataset.csv"


def exercise_dict(exercise):
    data = asdict(exercise)
    data["favorite"] = bool(data["favorite"])
    return data


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("EXERXEYE_SECRET", "exerx-eye-local-dev-change-me"),
        DATABASE=Path(os.getenv("EXERCISE_DB_PATH", str(DEFAULT_DB_PATH))),
        CSV_PATH=Path(os.getenv("EXERCISE_CSV_PATH", str(DEFAULT_CSV_PATH))),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
    )
    if test_config:
        app.config.update(test_config)

    bootstrap_db = ExerxEye(Path(app.config["DATABASE"]))
    try:
        csv_path = Path(app.config["CSV_PATH"])
        if bootstrap_db.count() == 0 and csv_path.exists():
            bootstrap_db.import_csv(csv_path)
    finally:
        bootstrap_db.close()

    def get_db() -> ExerxEye:
        if "db" not in g:
            g.db = ExerxEye(Path(app.config["DATABASE"]))
        return g.db

    def user_id() -> int | None:
        return int(g.user["id"]) if getattr(g, "user", None) is not None else None

    def safe_next(value: str | None) -> str | None:
        if not value:
            return None
        parsed = urlparse(value)
        if parsed.netloc or not value.startswith("/") or value.startswith("//"):
            return None
        return value

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                if request.headers.get("X-Requested-With") == "fetch":
                    return jsonify(error="Login required", login=url_for("login")), 401
                flash("Log in to use your private training workspace.", "info")
                return redirect(url_for("login", next=request.full_path.rstrip("?")))
            return view(*args, **kwargs)
        return wrapped

    @app.teardown_appcontext
    def close_db(_error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.before_request
    def load_logged_in_user():
        uid = session.get("user_id")
        g.user = get_db().user_by_id(int(uid)) if uid else None
        if uid and g.user is None:
            session.clear()

    @app.context_processor
    def inject_globals():
        prefs = get_db().user_preferences(user_id()) if g.user is not None else {"weekly_goal": 3, "default_rest": 60}
        return {
            "app_name": "ExerxEye",
            "app_tagline": "Exercise Intelligence & Analytics",
            "current_user": g.user,
            "user_preferences": prefs,
        }

    # ---------- Authentication ----------
    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if g.user is not None:
            return redirect(url_for("index"))
        next_url = safe_next(request.values.get("next"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")
            error = None
            if len(username) < 3:
                error = "Username must be at least 3 characters."
            elif len(password) < 8:
                error = "Password must be at least 8 characters."
            elif password != confirm:
                error = "Passwords do not match."
            if error:
                flash(error, "error")
            else:
                try:
                    uid = get_db().create_user(
                        username,
                        generate_password_hash(password, method="scrypt"),
                    )
                except ValueError as exc:
                    flash(str(exc), "error")
                else:
                    session.clear()
                    session["user_id"] = uid
                    session.permanent = True
                    flash("Account created. Your training data is now private to this profile.", "success")
                    return redirect(next_url or url_for("dashboard"))
        return render_template("signup.html", next_url=next_url)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user is not None:
            return redirect(url_for("index"))
        next_url = safe_next(request.values.get("next"))
        if request.method == "POST":
            login_value = request.form.get("login", "").strip()
            password = request.form.get("password", "")
            account = get_db().user_by_login(login_value)
            if account is None or not check_password_hash(account["password_hash"], password):
                flash("Incorrect username or password.", "error")
            else:
                session.clear()
                session["user_id"] = int(account["id"])
                session.permanent = True
                flash(f"Welcome back, {account['username']}.", "success")
                return redirect(next_url or url_for("dashboard"))
        return render_template("login.html", next_url=next_url)

    @app.post("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("index"))

    @app.get("/account")
    @login_required
    def account():
        db = get_db()
        uid = user_id()
        return render_template(
            "account.html",
            stats=db.stats(uid),
            workouts=db.list_user_workouts(uid),
            summary=db.user_progress_summary(uid),
            preferences=db.user_preferences(uid),
        )

    @app.post("/account/preferences")
    @login_required
    def update_preferences():
        weekly_goal = request.form.get("weekly_goal", 3, type=int) or 3
        default_rest = request.form.get("default_rest", 60, type=int) or 60
        prefs = get_db().update_user_preferences(user_id(), weekly_goal, default_rest)
        flash(f"Preferences saved: {prefs['weekly_goal']} sessions/week · {prefs['default_rest']}s rest.", "success")
        return redirect(url_for("account"))

    @app.route("/planner", methods=["GET", "POST"])
    @login_required
    def planner():
        db = get_db()
        uid = user_id()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if request.method == "POST":
            for weekday in range(7):
                raw = request.form.get(f"day_{weekday}", "").strip()
                workout_id = int(raw) if raw.isdigit() else None
                if not db.set_user_schedule(uid, weekday, workout_id):
                    flash(f"Could not save {days[weekday]} schedule.", "error")
                    break
            else:
                flash("Weekly plan saved.", "success")
                return redirect(url_for("planner"))
        schedule = {int(row["weekday"]): row for row in db.user_schedule(uid)}
        return render_template(
            "planner.html",
            days=days,
            schedule=schedule,
            workouts=db.list_user_workouts(uid),
            week_goal=db.user_week_goal(uid),
            today_index=date.today().weekday(),
        )

    @app.get("/dashboard")
    @login_required
    def dashboard():
        db = get_db()
        uid = user_id()
        data = db.user_dashboard(uid)
        data["schedule_map"] = {int(row["weekday"]): row for row in data["schedule"]}
        data["today_index"] = date.today().weekday()
        data["today_plan"] = data["schedule_map"].get(data["today_index"])
        data["next_workout"] = data["today_plan"] or data["last_workout"]
        trend = [dict(row) for row in data["trend"]]
        trend_max = max([float(row["volume"]) for row in trend], default=0.0)
        return render_template(
            "dashboard.html",
            dashboard=data,
            trend=trend,
            trend_max=trend_max,
        )

    # ---------- Exercise discovery ----------
    @app.get("/")
    def index():
        db = get_db()
        uid = user_id()
        q = request.args.get("q", "").strip()
        field = request.args.get("field", "All")
        equipment = request.args.get("equipment", "All")
        muscle = request.args.get("muscle", "All")
        difficulty = request.args.get("difficulty", "All")
        favorites_only = request.args.get("favorites") == "1" and uid is not None
        try:
            limit = max(1, min(int(request.args.get("limit", 100)), 500))
        except ValueError:
            limit = 100
        exercises = db.query(
            text=q,
            field=field,
            equipment=equipment,
            muscle=muscle,
            difficulty=difficulty,
            favorites_only=favorites_only,
            limit=limit,
            user_id=uid,
        )
        stats = db.stats(uid)
        return render_template(
            "index.html",
            exercises=exercises,
            stats=stats,
            fields=list(SEARCHABLE.keys()),
            equipment_options=db.distinct("equipment"),
            muscle_options=db.distinct("main_muscle"),
            filters={
                "q": q,
                "field": field,
                "equipment": equipment,
                "muscle": muscle,
                "difficulty": difficulty,
                "favorites": favorites_only,
                "limit": limit,
            },
        )

    @app.get("/exercise/<int:exercise_id>")
    def exercise_detail(exercise_id: int):
        db = get_db()
        uid = user_id()
        exercise = db.get(exercise_id, uid)
        if exercise is None:
            abort(404)
        workouts = db.list_user_workouts(uid) if uid is not None else []
        related = [
            e for e in db.query(muscle=exercise.main_muscle or "All", limit=5, user_id=uid)
            if e.id != exercise.id
        ][:4]
        best = db.user_exercise_best(uid, exercise.id) if uid is not None else {
            "sets": 0, "sessions": 0, "max_weight": 0, "best_1rm": 0, "volume": 0,
        }
        history = db.user_progress(uid, exercise.id, 8) if uid is not None else []
        last_weight = float(history[0]["weight"]) if history else 0
        return render_template(
            "exercise.html",
            exercise=exercise,
            workouts=workouts,
            related=related,
            best=best,
            history=history,
            last_weight=last_weight,
        )

    @app.post("/favorite/<int:exercise_id>")
    @login_required
    def toggle_favorite(exercise_id: int):
        db = get_db()
        uid = user_id()
        if db.get(exercise_id, uid) is None:
            abort(404)
        favorite = db.toggle_favorite(exercise_id, uid)
        if request.headers.get("X-Requested-With") == "fetch" or request.accept_mimetypes.best == "application/json":
            return jsonify(favorite=favorite, favorites=db.stats(uid)["favorites"])
        flash("Added to favorites." if favorite else "Removed from favorites.", "success")
        return redirect(request.form.get("next") or url_for("exercise_detail", exercise_id=exercise_id))

    @app.get("/random")
    def random_page():
        db = get_db()
        uid = user_id()
        muscle = request.args.get("muscle") or None
        try:
            count = max(1, min(int(request.args.get("count", 6)), 24))
        except ValueError:
            count = 6
        rows = db.random(muscle, count, user_id=uid)
        return render_template(
            "random.html",
            exercises=rows,
            muscles=db.distinct("main_muscle"),
            selected_muscle=muscle or "",
            count=count,
        )

    @app.get("/stats")
    def stats_page():
        return render_template("stats.html", stats=get_db().stats(user_id()))

    # ---------- Private workout workspace ----------
    @app.route("/workouts", methods=["GET", "POST"])
    @login_required
    def workouts():
        db = get_db()
        uid = user_id()
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            notes = request.form.get("notes", "").strip()
            try:
                workout_id = db.create_user_workout(uid, name, notes)
            except ValueError as exc:
                flash(str(exc), "error")
            else:
                flash(f"Created workout: {name}", "success")
                return redirect(url_for("workout_detail", workout_id=workout_id))
        return render_template(
            "workouts.html",
            workouts=db.list_user_workouts(uid),
            muscle_options=db.distinct("main_muscle"),
            equipment_options=db.distinct("equipment"),
        )

    @app.post("/workouts/generate")
    @login_required
    def generate_workout():
        db = get_db()
        uid = user_id()
        preset = request.form.get("preset", "full_body").strip()
        equipment = request.form.get("equipment", "All").strip() or "All"
        custom_muscle = request.form.get("muscle", "All").strip() or "All"
        count = request.form.get("count", 6, type=int) or 6
        count = max(3, min(count, 10))

        preset_muscles = {
            "full_body": ["Chest", "Back", "Thighs", "Hips", "Shoulder", "Upper Arms"],
            "upper": ["Chest", "Back", "Shoulder", "Upper Arms", "Forearm"],
            "lower": ["Thighs", "Hips", "Calves"],
            "push": ["Chest", "Shoulder", "Upper Arms"],
            "pull": ["Back", "Upper Arms", "Forearm"],
            "custom": [custom_muscle] if custom_muscle != "All" else [],
        }
        labels = {
            "full_body": "Full Body", "upper": "Upper Body", "lower": "Lower Body",
            "push": "Push", "pull": "Pull", "custom": custom_muscle if custom_muscle != "All" else "Custom",
        }
        muscles = preset_muscles.get(preset, preset_muscles["full_body"])
        chosen = []
        seen: set[int] = set()

        # First pass: spread the plan across the preset muscle groups.
        for muscle_name in muscles:
            pool = db.query(muscle=muscle_name, equipment=equipment, limit=500, user_id=uid)
            if pool:
                exercise = random.choice(pool)
                if exercise.id not in seen:
                    seen.add(exercise.id)
                    chosen.append(exercise)
                if len(chosen) >= count:
                    break

        # Second pass: fill remaining slots from the same focus/equipment constraints.
        if len(chosen) < count:
            if preset == "custom" and custom_muscle != "All":
                pool = db.query(muscle=custom_muscle, equipment=equipment, limit=1000, user_id=uid)
            else:
                pool = db.query(equipment=equipment, limit=1000, user_id=uid)
                if muscles:
                    pool = [exercise for exercise in pool if exercise.main_muscle in muscles]
            pool = [exercise for exercise in pool if exercise.id not in seen]
            random.shuffle(pool)
            chosen.extend(pool[: max(0, count - len(chosen))])

        if not chosen:
            flash("No exercises matched those generator filters.", "error")
            return redirect(url_for("workouts"))

        default_name = f"{labels.get(preset, 'Generated')} · {len(chosen)} moves"
        name = request.form.get("name", "").strip() or default_name
        notes = f"Generated from {labels.get(preset, 'custom')} focus" + (f" · {equipment}" if equipment != "All" else "")
        workout_id = db.create_user_workout(uid, name, notes)
        for exercise in chosen:
            reps = 12 if exercise.main_muscle in {"Calves", "Forearm"} else 10
            db.add_to_user_workout(uid, workout_id, exercise.id, 3, reps, 0)

        flash(f"Generated {name} with {len(chosen)} exercises. Review the targets before training.", "success")
        return redirect(url_for("workout_detail", workout_id=workout_id))

    @app.get("/workouts/<int:workout_id>")
    @login_required
    def workout_detail(workout_id: int):
        db = get_db()
        uid = user_id()
        workout = db.user_workout(uid, workout_id)
        if workout is None:
            abort(404)
        session_id = request.args.get("session", type=int)
        if session_id and db.user_session(uid, session_id) is None:
            session_id = None
        session_sets = db.user_session_sets(uid, session_id) if session_id else []
        sets_by_exercise: dict[int, list] = {}
        for row in session_sets:
            sets_by_exercise.setdefault(int(row["exercise_id"]), []).append(row)
        return render_template(
            "workout_detail.html",
            workout=workout,
            items=db.user_workout_detail(uid, workout_id),
            session_id=session_id,
            session_summary=db.user_session_summary(uid, workout_id, session_id),
            sets_by_exercise=sets_by_exercise,
            default_rest=db.user_preferences(uid)["default_rest"],
            celebrate=request.args.get("celebrate") == "1",
        )

    @app.post("/workouts/<int:workout_id>/add/<int:exercise_id>")
    @login_required
    def add_to_workout(workout_id: int, exercise_id: int):
        db = get_db()
        uid = user_id()
        workout = db.user_workout(uid, workout_id)
        exercise = db.get(exercise_id, uid)
        if workout is None or exercise is None:
            abort(404)
        sets = request.form.get("sets", 3, type=int) or 3
        reps = request.form.get("reps", 10, type=int) or 10
        weight = request.form.get("target_weight", 0, type=float) or 0
        db.add_to_user_workout(uid, workout_id, exercise_id, max(1, sets), max(1, reps), max(0, weight))
        flash(f"Added {exercise.exercise_name} to workout.", "success")
        return redirect(request.form.get("next") or url_for("workout_detail", workout_id=workout_id))

    @app.post("/workouts/<int:workout_id>/update")
    @login_required
    def update_workout(workout_id: int):
        db = get_db()
        try:
            updated = db.update_user_workout(
                user_id(), workout_id,
                request.form.get("name", ""),
                request.form.get("notes", ""),
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            if not updated:
                abort(404)
            flash("Workout details updated.", "success")
        return redirect(url_for("workout_detail", workout_id=workout_id))

    @app.post("/workouts/<int:workout_id>/item/<int:item_id>/update")
    @login_required
    def update_workout_item(workout_id: int, item_id: int):
        sets = request.form.get("sets", type=int) or 1
        reps = request.form.get("reps", type=int) or 1
        weight = request.form.get("target_weight", type=float) or 0
        if not get_db().update_user_workout_item(user_id(), workout_id, item_id, sets, reps, weight):
            abort(404)
        flash("Exercise target updated.", "success")
        return redirect(url_for("workout_detail", workout_id=workout_id))

    @app.post("/workouts/<int:workout_id>/item/<int:item_id>/move")
    @login_required
    def move_workout_item(workout_id: int, item_id: int):
        direction = request.form.get("direction", "down")
        if direction not in {"up", "down"}:
            abort(400)
        get_db().move_user_workout_item(user_id(), workout_id, item_id, direction)
        return redirect(url_for("workout_detail", workout_id=workout_id))

    @app.post("/workouts/<int:workout_id>/duplicate")
    @login_required
    def duplicate_workout(workout_id: int):
        db = get_db()
        try:
            new_id = db.duplicate_user_workout(user_id(), workout_id)
        except ValueError:
            abort(404)
        flash("Workout duplicated.", "success")
        return redirect(url_for("workout_detail", workout_id=new_id))

    @app.post("/workouts/<int:workout_id>/delete")
    @login_required
    def delete_workout(workout_id: int):
        db = get_db()
        uid = user_id()
        active = db.user_active_session(uid)
        if active is not None and active["workout_id"] == workout_id:
            flash("Finish or discard the active session before deleting this workout.", "error")
            return redirect(url_for("workout_detail", workout_id=workout_id, session=active["id"]))
        if db.delete_user_workout(uid, workout_id):
            flash("Workout deleted.", "success")
        return redirect(url_for("workouts"))

    @app.post("/workouts/<int:workout_id>/remove/<int:item_id>")
    @login_required
    def remove_from_workout(workout_id: int, item_id: int):
        if get_db().remove_from_user_workout(user_id(), workout_id, item_id):
            flash("Exercise removed from workout.", "success")
        return redirect(url_for("workout_detail", workout_id=workout_id))

    @app.post("/workouts/<int:workout_id>/start")
    @login_required
    def start_session(workout_id: int):
        db = get_db()
        uid = user_id()
        active = db.user_active_session(uid)
        if active is not None:
            flash(f"You already have an active session: {active['workout_name']}. Resume or discard it first.", "info")
            return redirect(url_for("workout_detail", workout_id=active["workout_id"], session=active["id"]))
        try:
            session_id = db.start_user_session(uid, workout_id)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("workouts"))
        flash("Workout session started.", "success")
        return redirect(url_for("workout_detail", workout_id=workout_id, session=session_id))

    @app.post("/sessions/<int:session_id>/log/<int:exercise_id>")
    @login_required
    def log_set(session_id: int, exercise_id: int):
        db = get_db()
        uid = user_id()
        active = db.user_session(uid, session_id)
        if active is None:
            abort(404)
        if active["completed_at"] is not None:
            flash("That session is already complete.", "error")
            return redirect(url_for("progress_page"))
        reps = request.form.get("reps", type=int)
        weight = request.form.get("weight", 0, type=float) or 0
        rir = request.form.get("rir", type=int)
        note = request.form.get("note", "")
        if not reps or reps < 1:
            flash("Reps must be at least 1.", "error")
        elif rir is not None and not 0 <= rir <= 10:
            flash("RIR must be between 0 and 10.", "error")
        else:
            before = db.user_exercise_best(uid, exercise_id)["best_1rm"]
            set_number = db.user_session_set_count(uid, session_id, exercise_id) + 1
            db.log_user_set(uid, session_id, exercise_id, set_number, reps, max(0, weight), rir, note)
            after = db.user_exercise_best(uid, exercise_id)["best_1rm"]
            effort = f" · {rir} RIR" if rir is not None else ""
            if after > before and weight > 0:
                flash(f"New estimated 1RM PR: {after:g} lb. Set {set_number} logged{effort}.", "success")
            else:
                flash(f"Logged set {set_number}: {reps} reps @ {weight:g}{effort}.", "success")
        return redirect(url_for("workout_detail", workout_id=active["workout_id"], session=session_id))

    @app.post("/sessions/<int:session_id>/finish")
    @login_required
    def finish_session(session_id: int):
        db = get_db()
        uid = user_id()
        active = db.user_session(uid, session_id)
        if active is None:
            abort(404)
        db.complete_user_session(uid, session_id)
        flash("Workout complete — review the session while it is fresh.", "success")
        return redirect(url_for("session_summary", session_id=session_id, celebrate=1))

    @app.post("/sessions/<int:session_id>/discard")
    @login_required
    def discard_session(session_id: int):
        if get_db().discard_user_session(user_id(), session_id):
            flash("Active session discarded.", "success")
        else:
            flash("Only an unfinished session can be discarded.", "error")
        return redirect(url_for("dashboard"))

    @app.route("/sessions/<int:session_id>/summary", methods=["GET", "POST"])
    @login_required
    def session_summary(session_id: int):
        db = get_db()
        uid = user_id()
        review = db.user_session_review(uid, session_id)
        if review is None:
            abort(404)
        if request.method == "POST":
            raw_rpe = request.form.get("session_rpe", "").strip()
            session_rpe = int(raw_rpe) if raw_rpe.isdigit() else None
            if session_rpe is not None and not 1 <= session_rpe <= 10:
                flash("Session RPE must be between 1 and 10.", "error")
            else:
                db.update_user_session_review(uid, session_id, session_rpe, request.form.get("note", ""))
                flash("Session review saved.", "success")
                return redirect(url_for("session_summary", session_id=session_id))
        return render_template(
            "session_summary.html",
            review=review,
            celebrate=request.args.get("celebrate") == "1",
        )

    @app.get("/progress")
    @login_required
    def progress_page():
        db = get_db()
        uid = user_id()
        exercise_id = request.args.get("exercise", type=int)
        days = request.args.get("days", 30, type=int)
        days = days if days in {7, 30, 90, 365} else 30
        rows = db.user_progress(uid, exercise_id, 500, days=days)
        trend = [dict(row) for row in db.user_volume_trend(uid, days)]
        trend_max = max([float(row["volume"]) for row in trend], default=0.0)
        return render_template(
            "progress.html",
            rows=rows,
            selected_exercise=exercise_id,
            exercises=db.query(limit=1000, user_id=uid),
            summary=db.user_progress_summary(uid, exercise_id, days=days),
            days=days,
            trend=trend,
            trend_max=trend_max,
            prs=db.user_recent_prs(uid, 8),
        )

    # ---------- Export center ----------
    @app.get("/exports")
    @login_required
    def exports_page():
        db = get_db()
        uid = user_id()
        return render_template(
            "exports.html",
            summary=db.user_progress_summary(uid),
            favorite_count=db.stats(uid)["favorites"],
            workout_count=len(db.list_user_workouts(uid)),
        )

    @app.get("/exports/progress.csv")
    @app.get("/progress/export.csv")
    @login_required
    def export_progress():
        db = get_db()
        uid = user_id()
        exercise_id = request.args.get("exercise", type=int)
        rows = db.user_progress(uid, exercise_id, 5000)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["exercise", "workout", "reps", "weight", "volume", "estimated_1rm", "rir", "note", "completed_at"])
        for row in rows:
            writer.writerow([
                row["exercise_name"], row["workout_name"], row["reps"], row["weight"],
                row["volume"], row["est_1rm"], row["rir"], row["note"], row["completed_at"],
            ])
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=exerxeye-progress.csv"},
        )

    @app.get("/exports/favorites.csv")
    @login_required
    def export_favorites():
        rows = get_db().query(favorites_only=True, limit=5000, user_id=user_id())
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "exercise", "main_muscle", "equipment", "difficulty", "mechanics", "force"])
        for e in rows:
            writer.writerow([e.id, e.exercise_name, e.main_muscle, e.equipment, e.difficulty, e.mechanics, e.force])
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=exerxeye-favorites.csv"},
        )

    @app.get("/exports/workouts.csv")
    @login_required
    def export_workouts():
        db = get_db()
        uid = user_id()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["workout", "notes", "exercise", "muscle", "equipment", "sets", "reps", "target_weight"])
        for workout in db.list_user_workouts(uid):
            detail = db.user_workout_detail(uid, workout["id"])
            if not detail:
                writer.writerow([workout["name"], workout["notes"], "", "", "", "", "", ""])
            for item in detail:
                writer.writerow([
                    workout["name"], workout["notes"], item["exercise_name"], item["main_muscle"],
                    item["equipment"], item["sets"], item["reps"], item["target_weight"],
                ])
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=exerxeye-workouts.csv"},
        )

    @app.get("/exports/account.json")
    @login_required
    def export_account():
        payload = get_db().user_export_bundle(user_id())
        return Response(
            json.dumps(payload, indent=2, default=str),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=exerxeye-account-export.json"},
        )

    @app.get("/exports/library.csv")
    def export_library():
        rows = get_db().query(limit=5000, user_id=user_id())
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "exercise", "equipment", "main_muscle", "difficulty", "mechanics", "force", "utility"])
        for e in rows:
            writer.writerow([e.id, e.exercise_name, e.equipment, e.main_muscle, e.difficulty, e.mechanics, e.force, e.utility])
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=exerxeye-exercise-library.csv"},
        )

    # ---------- Installable web app ----------
    @app.get("/service-worker.js")
    def service_worker():
        response = app.send_static_file("service-worker.js")
        response.headers["Service-Worker-Allowed"] = "/"
        response.headers["Cache-Control"] = "no-cache"
        return response

    # ---------- JSON API ----------
    @app.get("/health")
    def health():
        db = get_db()
        return jsonify({**db.health(), "schema_version": db.schema_version()})

    @app.get("/api")
    def api_root():
        return jsonify(
            name="ExerxEye Flask API",
            version="10.0.0",
            endpoints=[
                "/api/exercises", "/api/exercises/<id>", "/api/random",
                "/api/muscles", "/api/stats", "/health",
            ],
        )

    @app.get("/api/exercises")
    def api_exercises():
        db = get_db()
        try:
            limit = max(1, min(int(request.args.get("limit", 100)), 500))
        except ValueError:
            limit = 100
        rows = db.query(
            text=request.args.get("q", ""),
            field=request.args.get("field", "All"),
            muscle=request.args.get("muscle", "All"),
            equipment=request.args.get("equipment", "All"),
            difficulty=request.args.get("difficulty", "All"),
            favorites_only=request.args.get("favorites") == "1" and g.user is not None,
            limit=limit,
            user_id=user_id(),
        )
        return jsonify(results=[exercise_dict(e) for e in rows])

    @app.get("/api/exercises/<int:exercise_id>")
    def api_exercise(exercise_id: int):
        exercise = get_db().get(exercise_id, user_id())
        if exercise is None:
            return jsonify(error="Exercise not found"), 404
        return jsonify(exercise_dict(exercise))

    @app.get("/api/random")
    def api_random():
        db = get_db()
        muscle = request.args.get("muscle") or None
        count = request.args.get("count", 1, type=int) or 1
        count = max(1, min(count, 24))
        return jsonify(results=[exercise_dict(e) for e in db.random(muscle, count, user_id=user_id())])

    @app.get("/api/muscles")
    def api_muscles():
        return jsonify(muscles=get_db().distinct("main_muscle"))

    @app.get("/api/stats")
    def api_stats():
        stats = get_db().stats(user_id())
        return jsonify(
            **{k: v for k, v in stats.items() if not k.startswith("by_")},
            by_muscle=[dict(r) for r in stats["by_muscle"]],
            by_equipment=[dict(r) for r in stats["by_equipment"]],
            by_difficulty=[dict(r) for r in stats["by_difficulty"]],
        )

    # Backward-compatible public endpoints.
    @app.get("/exercises")
    def legacy_exercises():
        return api_exercises()

    @app.get("/exercises/<int:exercise_id>")
    def legacy_exercise(exercise_id: int):
        return api_exercise(exercise_id)

    @app.get("/muscles")
    def legacy_muscles():
        return api_muscles()

    @app.get("/one_exercise_per_muscle")
    def legacy_one():
        muscle = request.args.get("muscle") or None
        return jsonify(results=[exercise_dict(e) for e in get_db().random(muscle, 1, user_id=user_id())])

    @app.get("/six_exercises_per_muscle")
    def legacy_six():
        muscle = request.args.get("muscle") or None
        return jsonify(results=[exercise_dict(e) for e in get_db().random(muscle, 6, user_id=user_id())])

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=os.getenv("FLASK_DEBUG") == "1")
