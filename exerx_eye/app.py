from __future__ import annotations

from pathlib import Path
from rich.markup import escape
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Select, Static, TabbedContent, TabPane

from .db import Exercise, ExerxEye, SEARCHABLE

APP_DIR = Path.home() / ".local" / "share" / "exerx-eye"
DEFAULT_DB = APP_DIR / "exercises.db"
SPARK = "▁▂▃▄▅▆▇█"


def bars(rows, label_key: str, value_key: str, width: int = 28, limit: int | None = None) -> str:
    rows = list(rows)[:limit] if limit else list(rows)
    if not rows:
        return "No data yet."
    maximum = max(int(r[value_key]) for r in rows) or 1
    lines = []
    for r in rows:
        label = str(r[label_key] or "Unknown")
        value = int(r[value_key])
        n = max(1, round((value / maximum) * width)) if value else 0
        lines.append(f"{label[:18]:<18} {'█' * n:<{width}} {value:>4}")
    return "\n".join(lines)


def sparkline(values: list[float]) -> str:
    if not values:
        return "No logged sets yet."
    lo, hi = min(values), max(values)
    if hi == lo:
        return SPARK[3] * len(values)
    return "".join(SPARK[round((v - lo) / (hi - lo) * (len(SPARK) - 1))] for v in values)


class ExerciseTUI(App):
    TITLE = "EXERXEYE — Exercise Intelligence & Analytics"
    SUB_TITLE = "EXERXEYE — Exercise Intelligence & Analytics"
    BINDINGS = [
        Binding("q", "quit", "Quit"), Binding("/", "focus_search", "Search"),
        Binding("r", "random_one", "Random"), Binding("6", "random_six", "Random ×6"),
        Binding("f", "favorite", "Favorite"), Binding("a", "add_to_workout", "Add → Workout"), Binding("x", "compare", "Compare"),
        Binding("e", "export", "Export"), Binding("c", "clear_filters", "Clear"),
        Binding("1", "show_tab('browse')", "Browse", show=False),
        Binding("2", "show_tab('muscles')", "Muscles", show=False),
        Binding("3", "show_tab('random')", "Random", show=False),
        Binding("4", "show_tab('workouts')", "Workouts", show=False),
        Binding("5", "show_tab('progress')", "Progress", show=False),
        Binding("6", "show_tab('stats')", "Stats", show=False),
        Binding("7", "show_tab('compare')", "Compare", show=False),
        Binding("8", "show_tab('system')", "System", show=False),
    ]

    CSS = """
    Screen { layout: vertical; }
    #filters, #random-controls, #workout-create, #log-controls { height: 3; padding: 0 1; }
    #filters Input { width: 2fr; }
    #filters Select { width: 1fr; margin-left: 1; }
    #browse-body, #random-body, #muscle-body, #workout-body, #progress-body { height: 1fr; }
    DataTable { width: 3fr; }
    .detail { width: 2fr; border-left: solid $primary; padding: 0 1; }
    .detail-title { text-style: bold; margin-bottom: 1; }
    .muted { color: $text-muted; }
    #muscle-list { width: 1fr; }
    #muscle-exercises { width: 2fr; }
    #muscle-detail { width: 2fr; }
    #random-controls Select { width: 1fr; margin-right: 1; }
    #random-help { width: 2fr; content-align: left middle; }
    #workout-name { width: 2fr; }
    #workout-create Button { width: 1fr; }
    #workout-list { width: 1fr; }
    #workout-exercises { width: 2fr; }
    #workout-panel { width: 2fr; }
    #log-controls Input { width: 1fr; margin-right: 1; }
    #progress-table { width: 3fr; }
    #progress-charts { width: 2fr; padding: 0 1; border-left: solid $primary; }
    #stats-view, #system-view { padding: 1 2; }
    """

    def __init__(self, db_path: Path = DEFAULT_DB):
        super().__init__()
        self.db = ExerxEye(db_path)
        self.current_rows: list[Exercise] = []
        self.random_rows: list[Exercise] = []
        self.selected_id: int | None = None
        self.active_workout_id: int | None = None
        self.active_session_id: int | None = None
        self.active_workout_exercise_id: int | None = None
        self.compare_ids: list[int] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="browse"):
            with TabPane("Browse", id="browse"):
                with Horizontal(id="filters"):
                    yield Input(placeholder="Search exercises…", id="search")
                    yield Select([(k, k) for k in SEARCHABLE], value="All", id="field", allow_blank=False)
                    yield Select([], prompt="Equipment", id="equipment")
                    yield Select([], prompt="Muscle", id="muscle")
                    yield Select([("All", "All"), *[(str(i), str(i)) for i in range(1, 6)]], value="All", id="difficulty", allow_blank=False)
                with Horizontal(id="browse-body"):
                    yield DataTable(id="results", cursor_type="row", zebra_stripes=True)
                    with VerticalScroll(classes="detail"):
                        yield Static("Select an exercise", classes="detail-title", id="detail-content")
            with TabPane("Muscles", id="muscles"):
                with Horizontal(id="muscle-body"):
                    yield DataTable(id="muscle-list", cursor_type="row", zebra_stripes=True)
                    yield DataTable(id="muscle-exercises", cursor_type="row", zebra_stripes=True)
                    with VerticalScroll(classes="detail"):
                        yield Static("Choose a muscle group", id="muscle-detail-content")
            with TabPane("Random", id="random"):
                with Horizontal(id="random-controls"):
                    yield Select([], prompt="Muscle / all", id="random-muscle")
                    yield Static("R = one random • 6 = six random • F = favorite • A = add to workout", id="random-help", classes="muted")
                with Horizontal(id="random-body"):
                    yield DataTable(id="random-results", cursor_type="row", zebra_stripes=True)
                    with VerticalScroll(classes="detail"):
                        yield Static("Generate a random exercise", id="random-detail-content")
            with TabPane("Workouts", id="workouts"):
                with Horizontal(id="workout-create"):
                    yield Input(placeholder="New workout name (Push Day, Pull Day…)", id="workout-name")
                    yield Button("Create Workout", id="create-workout", variant="primary")
                    yield Button("Start Session", id="start-session", variant="success")
                    yield Button("Finish Session", id="finish-session", variant="warning")
                with Horizontal(id="workout-body"):
                    yield DataTable(id="workout-list", cursor_type="row", zebra_stripes=True)
                    yield DataTable(id="workout-exercises", cursor_type="row", zebra_stripes=True)
                    with Vertical(id="workout-panel", classes="detail"):
                        yield Static("Select a workout. In Browse, press A to add the selected exercise.", id="workout-status")
                        with Horizontal(id="log-controls"):
                            yield Input(value="10", placeholder="Reps", id="log-reps", type="integer")
                            yield Input(value="0", placeholder="Weight", id="log-weight", type="number")
                            yield Button("Log Set", id="log-set", variant="primary")
            with TabPane("Progress", id="progress"):
                with Horizontal(id="progress-body"):
                    yield DataTable(id="progress-table", cursor_type="row", zebra_stripes=True)
                    yield Static(id="progress-charts")
            with TabPane("Statistics", id="stats"):
                yield Static(id="stats-view")
            with TabPane("Compare", id="compare"):
                yield Static("Select an exercise and press X. Add two exercises to compare them.", id="compare-view", classes="detail")
            with TabPane("System", id="system"):
                yield Static(id="system-view")
        yield Footer()

    def on_mount(self) -> None:
        if not self.db.count():
            self.notify("Database is empty. Import the CSV first.", severity="warning", timeout=8)
        self._setup_tables(); self._load_selects()
        self.refresh_browse(); self.refresh_muscles(); self.refresh_workouts(); self.refresh_progress(); self.refresh_stats(); self.refresh_compare(); self.refresh_system()

    def _setup_tables(self) -> None:
        for table_id in ("results", "muscle-exercises", "random-results"):
            self.query_one(f"#{table_id}", DataTable).add_columns("★", "Exercise", "Muscle", "Equipment", "Diff", "Force")
        self.query_one("#muscle-list", DataTable).add_columns("Muscle", "Exercises")
        self.query_one("#workout-list", DataTable).add_columns("Workout", "Exercises", "Created")
        self.query_one("#workout-exercises", DataTable).add_columns("#", "Exercise", "Sets", "Reps", "Target")
        self.query_one("#progress-table", DataTable).add_columns("When", "Workout", "Exercise", "Reps", "Weight", "Volume", "Est 1RM")

    def _load_selects(self) -> None:
        eq = [("All", "All")] + [(x, x) for x in self.db.distinct("equipment")]
        muscles = [("All", "All")] + [(x, x) for x in self.db.distinct("main_muscle")]
        for ident, opts in (("#equipment", eq), ("#muscle", muscles), ("#random-muscle", muscles)):
            sel=self.query_one(ident, Select); sel.set_options(opts); sel.value="All"

    def _fill_exercise_table(self, table: DataTable, rows: list[Exercise]) -> None:
        table.clear()
        for e in rows:
            table.add_row("★" if e.favorite else "", e.exercise_name, e.main_muscle, e.equipment, str(e.difficulty), e.force, key=str(e.id))

    def refresh_browse(self) -> None:
        def val(id_: str, default="All"):
            v=self.query_one(id_, Select).value
            return default if v is Select.BLANK else str(v)
        self.current_rows=self.db.query(text=self.query_one("#search", Input).value, field=val("#field"), equipment=val("#equipment"), muscle=val("#muscle"), difficulty=val("#difficulty"))
        self._fill_exercise_table(self.query_one("#results", DataTable), self.current_rows)
        self.sub_title=f"SQLite • FastAPI • Textual • {len(self.current_rows)} shown / {self.db.count()} total"

    def refresh_muscles(self) -> None:
        table=self.query_one("#muscle-list", DataTable); table.clear()
        for r in self.db.stats()["by_muscle"]: table.add_row(r["main_muscle"], str(r["n"]), key=r["main_muscle"])

    def refresh_workouts(self) -> None:
        t=self.query_one("#workout-list", DataTable); t.clear()
        for r in self.db.list_workouts(): t.add_row(r["name"], str(r["exercise_count"]), str(r["created_at"])[:10], key=str(r["id"]))
        if self.active_workout_id: self._load_workout_detail(self.active_workout_id)

    def _load_workout_detail(self, workout_id:int) -> None:
        self.active_workout_id=workout_id
        rows=self.db.workout_detail(workout_id); t=self.query_one("#workout-exercises", DataTable); t.clear()
        for r in rows:
            target=f"{r['target_weight']:g}" if r['target_weight'] else "—"
            t.add_row(str(r["position"]), r["exercise_name"], str(r["sets"]), str(r["reps"]), target, key=str(r["exercise_id"]))
        state=f"Workout #{workout_id} • {len(rows)} exercises"
        if self.active_session_id: state += f"\n[b green]LIVE SESSION #{self.active_session_id}[/b green] • select an exercise and log sets"
        self.query_one("#workout-status", Static).update(state)

    def refresh_progress(self) -> None:
        rows=self.db.progress(limit=100); t=self.query_one("#progress-table", DataTable); t.clear()
        for r in rows:
            t.add_row(str(r["completed_at"])[:16], r["workout_name"], r["exercise_name"], str(r["reps"]), f"{r['weight']:g}", f"{r['volume']:g}", f"{r['est_1rm']:g}")
        chronological=list(reversed(rows))
        volumes=[float(r["volume"]) for r in chronological]
        one_rm=[float(r["est_1rm"]) for r in chronological if float(r["est_1rm"])>0]
        total=sum(volumes)
        chart=f"""[b]TRAINING PROGRESS[/b]\n\nLogged sets   [b]{len(rows)}[/b]\nTotal volume  [b]{total:,.0f}[/b]\n\n[b]Volume trend[/b]\n{sparkline(volumes[-48:])}\n\n[b]Estimated 1RM trend[/b]\n{sparkline(one_rm[-48:])}\n\n[s dim]Each block is one logged set. Charts update as training data is recorded.[/s dim]"""
        self.query_one("#progress-charts", Static).update(chart)

    def refresh_stats(self) -> None:
        s=self.db.stats()
        diff=bars(s["by_difficulty"], "difficulty", "n", width=22)
        muscle=bars(s["by_muscle"], "main_muscle", "n", width=28)
        equip=bars(s["by_equipment"], "equipment", "n", width=28, limit=10)
        self.query_one("#stats-view", Static).update(f"""[b]DATABASE ANALYTICS[/b]\nExercises [b]{s['exercises']}[/b]   Unique names [b]{s['names']}[/b]   Equipment [b]{s['equipment']}[/b]   Muscle groups [b]{s['muscles']}[/b]   Favorites [b]{s['favorites']}[/b]   Avg difficulty [b]{s['avg_difficulty']}/5[/b]\n\n[b]DIFFICULTY DISTRIBUTION[/b]\n{diff}\n\n[b]EXERCISES BY MAIN MUSCLE[/b]\n{muscle}\n\n[b]TOP EQUIPMENT[/b]\n{equip}""")


    def refresh_compare(self) -> None:
        exercises=[self.db.get(i) for i in self.compare_ids]
        exercises=[e for e in exercises if e]
        if not exercises:
            self.query_one("#compare-view", Static).update("[b]EXERCISE COMPARISON[/b]\n\nSelect an exercise anywhere and press [b]X[/b]. Add a second exercise to compare them side-by-side.")
            return
        if len(exercises)==1:
            e=exercises[0]
            self.query_one("#compare-view", Static).update(f"[b]EXERCISE COMPARISON[/b]\n\nSelected: [b]{escape(e.exercise_name)}[/b]\n\nSelect another exercise and press [b]X[/b].")
            return
        a,b=exercises[-2],exercises[-1]
        rows=[
            ("Exercise",a.exercise_name,b.exercise_name), ("Main muscle",a.main_muscle,b.main_muscle),
            ("Equipment",a.equipment,b.equipment), ("Difficulty",f"{a.difficulty}/5",f"{b.difficulty}/5"),
            ("Mechanics",a.mechanics,b.mechanics), ("Force",a.force,b.force),
            ("Utility",a.utility,b.utility), ("Targets",a.target_muscles,b.target_muscles),
            ("Secondary",a.secondary_muscles,b.secondary_muscles),
        ]
        width=30
        lines=[f"{'ATTRIBUTE':<14} {'A':<{width}} {'B':<{width}}", "─"*(16+width*2)]
        for label,av,bv in rows:
            lines.append(f"{label:<14} {str(av or '—')[:width]:<{width}} {str(bv or '—')[:width]:<{width}}")
        lines += ["", "[b]A preparation[/b]", escape(a.preparation or '—'), "", "[b]B preparation[/b]", escape(b.preparation or '—')]
        self.query_one("#compare-view", Static).update("\n".join(lines))

    def refresh_system(self) -> None:
        h=self.db.health(); size=h["db_size_bytes"]/1024
        self.query_one("#system-view", Static).update(f"""[b]SYSTEM STATUS[/b]\n\nDatabase        [b green]● {h['database']}[/b green]\nSQLite latency  [b]{h['latency_ms']} ms[/b]\nDatabase size   [b]{size:,.1f} KB[/b]\nExercises       [b]{h['exercises']}[/b]\nWorkouts        [b]{h['workouts']}[/b]\nCompleted       [b]{h['sessions']} sessions[/b]\nLogged sets     [b]{h['sets']}[/b]\nSchema version  [b]{self.db.schema_version()}[/b]\n\n[b]ARCHITECTURE[/b]\n\nExercise CSV ──► SQLite Repository ──► Textual TUI\n                    │\n                    ├──► Workouts ─► Sessions ─► Sets ─► Progress\n                    │\n                    └──► FastAPI REST service ─► Docker\n\n[s dim]Run `exerx-eye doctor` for the same checks from the shell.[/s dim]""")

    @staticmethod
    def detail_markup(e: Exercise) -> str:
        star=" ★" if e.favorite else ""
        def s(v): return escape(v or "—")
        return f"""[b]{s(e.exercise_name)}{star}[/b]\n[s dim]ID {e.id} • Difficulty {e.difficulty}/5[/s dim]\n\n[b]Main muscle[/b]\n{s(e.main_muscle)}\n\n[b]Targets[/b]\n{s(e.target_muscles)}\n\n[b]Equipment[/b]\n{s(e.equipment)}\n\n[b]Profile[/b]\n{s(e.utility)} • {s(e.mechanics)} • {s(e.force)}\n\n[b]Preparation[/b]\n{s(e.preparation)}\n\n[b]Execution[/b]\n{s(e.execution)}\n\n[b]Synergists[/b]\n{s(e.synergist_muscles)}\n\n[b]Stabilizers[/b]\n{s(e.stabilizer_muscles)}\n\n[b]Secondary[/b]\n{s(e.secondary_muscles)}\n\n[s dim]F favorite • A add to active workout • X compare[/s dim]"""

    def _show_detail(self, exercise_id:int, target:str) -> None:
        e=self.db.get(exercise_id)
        if e: self.selected_id=e.id; self.query_one(target, Static).update(self.detail_markup(e))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id=="search": self.refresh_browse()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id in {"field","equipment","muscle","difficulty"}: self.refresh_browse()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        tid=event.data_table.id; key=str(event.row_key.value)
        if tid=="results": self._show_detail(int(key), "#detail-content")
        elif tid=="random-results": self._show_detail(int(key), "#random-detail-content")
        elif tid=="muscle-exercises": self._show_detail(int(key), "#muscle-detail-content")
        elif tid=="muscle-list":
            rows=self.db.query(muscle=key); self._fill_exercise_table(self.query_one("#muscle-exercises", DataTable), rows)
            self.query_one("#muscle-detail-content", Static).update(f"[b]{escape(key)}[/b]\n\n{len(rows)} exercises\n\n{bars([{'label':str(i)+'★','n':sum(1 for e in rows if e.difficulty==i)} for i in range(1,6)], 'label','n',18)}")
        elif tid=="workout-list": self._load_workout_detail(int(key))
        elif tid=="workout-exercises": self.active_workout_exercise_id=int(key); self.selected_id=int(key); self._load_workout_detail(self.active_workout_id or 0)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid=event.button.id
        if bid=="create-workout":
            name=self.query_one("#workout-name", Input).value.strip()
            if not name: self.notify("Enter a workout name", severity="warning"); return
            self.active_workout_id=self.db.create_workout(name); self.query_one("#workout-name", Input).value=""; self.refresh_workouts(); self.notify(f"Created {name}")
        elif bid=="start-session":
            if not self.active_workout_id: self.notify("Select a workout first", severity="warning"); return
            self.active_session_id=self.db.start_session(self.active_workout_id); self._load_workout_detail(self.active_workout_id); self.notify("Workout session started")
        elif bid=="finish-session":
            if not self.active_session_id: self.notify("No live session", severity="warning"); return
            self.db.complete_session(self.active_session_id); self.active_session_id=None; self.refresh_progress(); self.refresh_system(); self._load_workout_detail(self.active_workout_id or 0); self.notify("Workout completed")
        elif bid=="log-set":
            if not self.active_session_id or not self.active_workout_exercise_id: self.notify("Start a session and select an exercise", severity="warning"); return
            try:
                reps=int(self.query_one("#log-reps", Input).value); weight=float(self.query_one("#log-weight", Input).value or 0)
                set_no=self.db.session_set_count(self.active_session_id, self.active_workout_exercise_id)+1
                self.db.log_set(self.active_session_id, self.active_workout_exercise_id, set_no, reps, weight)
                self.refresh_progress(); self.refresh_system(); self.notify(f"Logged set {set_no}: {reps} reps @ {weight:g}")
            except ValueError: self.notify("Reps and weight must be numbers", severity="error")

    def action_focus_search(self): self.query_one("#search", Input).focus()
    def action_show_tab(self, tab_id:str): self.query_one(TabbedContent).active=tab_id

    def action_clear_filters(self):
        self.query_one("#search", Input).value=""
        for ident in ("#field","#equipment","#muscle","#difficulty"): self.query_one(ident, Select).value="All"
        self.refresh_browse()

    def _random(self, count:int):
        v=self.query_one("#random-muscle", Select).value; muscle=None if v in {Select.BLANK,"All"} else str(v)
        self.random_rows=self.db.random(muscle, count); self._fill_exercise_table(self.query_one("#random-results", DataTable), self.random_rows)
        if self.random_rows: self._show_detail(self.random_rows[0].id, "#random-detail-content")
        self.query_one(TabbedContent).active="random"
    def action_random_one(self): self._random(1)
    def action_random_six(self): self._random(6)

    def action_favorite(self):
        if not self.selected_id: self.notify("Select an exercise first", severity="warning"); return
        enabled=self.db.toggle_favorite(self.selected_id); self.refresh_browse(); self.refresh_stats(); self.notify("Added to favorites" if enabled else "Removed from favorites")


    def action_compare(self):
        if not self.selected_id:
            self.notify("Select an exercise first", severity="warning"); return
        if self.selected_id in self.compare_ids:
            self.compare_ids.remove(self.selected_id)
        else:
            self.compare_ids.append(self.selected_id)
            self.compare_ids=self.compare_ids[-2:]
        self.refresh_compare(); self.query_one(TabbedContent).active="compare"

    def action_add_to_workout(self):
        if not self.selected_id: self.notify("Select an exercise first", severity="warning"); return
        if not self.active_workout_id: self.query_one(TabbedContent).active="workouts"; self.notify("Create or select a workout first", severity="warning"); return
        self.db.add_to_workout(self.active_workout_id, self.selected_id); self.refresh_workouts(); self.notify("Exercise added to workout")

    def action_export(self):
        path=APP_DIR/"exports"/"exercises.csv"; n=self.db.export_rows(self.db.query(limit=100000), path); self.notify(f"Exported {n} rows → {path}", timeout=6)

    def on_unmount(self): self.db.close()
