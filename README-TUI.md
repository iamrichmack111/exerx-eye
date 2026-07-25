# ExerxEye

**Exercise Intelligence & Analytics**

ExerxEye is a terminal-first training intelligence platform that combines exercise discovery, workout construction, persistent set history, progress analytics, comparison tools, a REST API, and operational health diagnostics.

## Product surfaces

- `exerx-eye tui` — keyboard-first Textual interface
- `exerx-eye search` — fast exercise discovery
- `exerx-eye random` — randomized exercise selection
- `exerx-eye stats` — dataset/training analytics
- `exerx-eye doctor` — database/system health checks
- FastAPI REST service for programmatic access


# ExerxEye v3.0

A portfolio-grade terminal-first exercise platform built from a 617-row exercise dataset.

## What v3 adds

- **Real terminal charts**: muscle, equipment, and difficulty bar charts
- **Progress plots**: Unicode sparklines for training volume and estimated 1RM
- **Workout Builder**: create workouts and add exercises directly from Browse with `A`
- **Live workout logging**: start a session, select an exercise, log reps/weight, finish the workout
- **Progress tab**: set history, volume, estimated 1RM, and trends
- **System tab**: DB health, latency, size, schema version, and architecture view
- **Schema migrations**: versioned `schema_migrations` table
- **Unified SQLite data layer** shared by the TUI and FastAPI
- **CLI surface**: search, random, stats, doctor, export, import, tui
- **Docker Compose API** with persistent volume and `/health` healthcheck
- Existing favorites, CSV export, randomizer, filters, muscle browser, and full exercise instructions

## Architecture

```text
617-row CSV ──► SQLite Repository ─────────► Textual TUI
                   │                           │
                   │                           ├── Browse / Random / Muscles
                   │                           ├── Workouts / Live Sessions
                   │                           ├── Progress / Charts
                   │                           └── Stats / System Health
                   │
                   ├────────► FastAPI REST API ──► Docker
                   │
                   └────────► CLI / doctor / export
```

## Install and launch

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
exerx-eye import data/gym_exercise_dataset.csv
exerx-eye tui
```

The old command still works:

```bash
exerx-eye --csv data/gym_exercise_dataset.csv --import-only
exerx-eye
```

## CLI examples

```bash
exerx-eye search "bench press"
exerx-eye random --muscle Chest --count 6
exerx-eye stats
exerx-eye doctor
exerx-eye export exercises.csv
```

## Workout workflow

1. Open **Workouts** and create a workout.
2. Return to **Browse**, select an exercise, press `A`.
3. Repeat for the rest of the workout.
4. In **Workouts**, select the workout and click **Start Session**.
5. Select an exercise, enter reps and weight, and click **Log Set**.
6. Click **Finish Session**.
7. Open **Progress** to see history and trend plots.

## API / Docker

```bash
docker compose up --build -d
curl http://localhost:8000/health
curl 'http://localhost:8000/exercises?q=bench&limit=5'
curl http://localhost:8000/stats
```

Interactive Swagger docs are at `http://localhost:8000/docs`.
