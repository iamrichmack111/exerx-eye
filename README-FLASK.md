# ExerxEye Flask Web App

The original ExerxEye SQLite data layer and terminal tools are preserved, but the web service is now Flask instead of FastAPI and includes a full browser interface.

## Web features

- Browse and search the full exercise database.
- Filter by field, muscle, equipment, difficulty, and favorites.
- Exercise detail pages with preparation/execution instructions.
- Toggle favorites.
- Generate random exercises by muscle.
- Create workouts and add exercises to them.
- Start a workout session, log reps/weight, and finish the session.
- Review progress and training volume.
- View database analytics.
- JSON API under `/api/*` plus `/health`.
- Docker/Gunicorn deployment.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:8000
```

## Production-style run

```bash
gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 4 app:app
```

## Docker

```bash
docker compose up --build
```

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

## Environment variables

```text
EXERCISE_DB_PATH   SQLite database path (default: instance/exercises.db)
EXERCISE_CSV_PATH  Seed CSV path (default: data/gym_exercise_dataset.csv)
EXERXEYE_SECRET    Flask secret key
PORT               Development-server port (default: 8000)
FLASK_DEBUG        Set to 1 for Flask debug mode
```


## Themes

The web UI includes 10 built-in themes: Obsidian Mint, Midnight Neon, Royal Purple, Crimson Forge, Solar Gold, Arctic Ice, Sakura Night, Terminal Green, Deep Ocean, and Sandstone. The selected theme is saved in browser localStorage and restored automatically.
## V8 account + appearance update

- **No email required:** sign up and log in with a username and password only.
- **Dark mode:** a dedicated Light/Dark toggle appears in the main app and auth screens, follows the system preference on first use, and remembers the choice locally.
- Existing databases remain compatible; legacy email values are retained internally only for migration compatibility and are no longer shown, used for login, or included in account exports.

