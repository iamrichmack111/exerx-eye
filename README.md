# ExerxEye

**Exercise Intelligence & Analytics**

ExerxEye is a terminal-first exercise discovery, workout-building, and training-progress application. It combines a searchable exercise database with workout planning, set logging, comparison tools, favorites, analytics, progress trends, a CLI, and an optional FastAPI service.

---

## What ExerxEye does

ExerxEye gives you several ways to work with the exercise dataset:

- Browse and search hundreds of exercises.
- Filter by muscle, equipment, difficulty, or searchable field.
- Read preparation and execution instructions.
- Favorite exercises for quick reference.
- Build named workouts.
- Add exercises from Browse directly into a selected workout.
- Start a live workout session.
- Log reps and weight for each set.
- Finish sessions and preserve workout history.
- Track training volume and estimated 1RM trends.
- Compare two exercises side-by-side.
- View exercise-database statistics and terminal-native charts.
- Use the same data from the CLI.
- Run the optional REST API with FastAPI/Docker.

---

# Installation

## 1. Create a virtual environment

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On every new terminal session, reactivate it with:

```bash
source .venv/bin/activate
```

## 2. Install ExerxEye

```bash
python -m pip install -U pip
python -m pip install -e .
```

## 3. Import the exercise dataset

```bash
exerx-eye import data/gym_exercise_dataset.csv
```

If the database already contains the dataset, the importer may report:

```text
Imported 0 exercises
```

That normally means duplicate exercises were skipped rather than the import failing.

## 4. Launch the TUI

```bash
exerx-eye tui
```

You can also inspect the available CLI commands with:

```bash
exerx-eye --help
```

---

# TUI overview

The interface contains these tabs:

```text
Browse
Muscles
Random
Workouts
Progress
Statistics
Compare
System
```

The footer also displays the most important keyboard shortcuts.

---

# Browse

The **Browse** tab is the main exercise explorer.

You can:

- Type in the search field.
- Choose which field to search.
- Filter by equipment.
- Filter by muscle.
- Filter by difficulty.
- Highlight a result to view the full exercise details.

The detail pane shows information such as:

- exercise name
- main muscle
- equipment
- difficulty
- mechanics
- force
- target muscles
- secondary muscles
- preparation
- execution instructions

## Browse keyboard controls

```text
↑ / ↓     Move through exercises
/         Focus the search box
A         Add selected exercise to the active workout
X         Add selected exercise to Compare
F         Toggle favorite
C         Clear filters
E         Export
R         Generate one random exercise
6         Generate six random exercises
Q         Quit
```

---

# Creating a workout

The workout builder uses a two-part workflow:

1. Create/select the workout in **Workouts**.
2. Add exercises to it from **Browse**.

This is intentional: Browse remains the searchable exercise catalog, while Workouts remains the planning/logging screen.

## Step 1 — Create a workout

Open the **Workouts** tab.

In the workout-name field, enter something like:

```text
Push Day
```

Then activate:

```text
Create Workout
```

The workout appears in the workout list.

## Step 2 — Select the workout

Highlight your new workout in the left-side workout list.

This makes it the active workout.

## Step 3 — Add exercises

Go back to **Browse**.

Highlight an exercise such as:

```text
Bench Press
```

Press:

```text
A
```

The selected exercise is added to the active workout.

Repeat this for every exercise you want.

Example:

```text
Push Day

Bench Press
Incline Dumbbell Press
Overhead Press
Lateral Raise
Tricep Pushdown
```

## Step 4 — Review the workout

Return to **Workouts**.

Select the workout again.

The middle table shows its exercises and programmed set/rep targets.

---

# Logging a workout session

Once a workout contains exercises:

## 1. Select the workout

Highlight the workout in the workout list.

## 2. Start the session

Activate:

```text
Start Session
```

The status panel indicates that a live session is active.

## 3. Select an exercise

Highlight an exercise in the workout-exercise table.

## 4. Enter reps and weight

Use the input fields for:

```text
Reps
Weight
```

Example:

```text
Reps:   8
Weight: 135
```

## 5. Log the set

Activate:

```text
Log Set
```

Repeat for every completed set.

For example:

```text
Bench Press
Set 1: 135 × 8
Set 2: 135 × 8
Set 3: 135 × 7
Set 4: 135 × 6
```

## 6. Finish the session

When the workout is complete, activate:

```text
Finish Session
```

The session is saved and becomes part of your progress history.

---

# Progress

The **Progress** tab uses your logged workout sets.

It shows:

- date/time
- workout
- exercise
- reps
- weight
- volume
- estimated 1RM

The right panel contains terminal-native trend plots.

## Volume

Set volume is calculated from:

```text
weight × reps
```

Logged sets contribute to the overall volume trend.

## Estimated 1RM

When weight is greater than zero, ExerxEye calculates an estimated one-repetition maximum for trend analysis.

The progress display is intended to show direction over time rather than replace professional programming or medical advice.

If the Progress tab is empty, complete at least one workout session with logged sets.

---

# Compare

The **Compare** tab compares exactly two selected exercises.

## How to select exercises

Go to **Browse**.

Highlight the first exercise and press:

```text
X
```

Highlight the second exercise and press:

```text
X
```

Now open **Compare**.

You will see the exercises side-by-side.

Comparison fields include:

```text
Exercise
Main muscle
Equipment
Difficulty
Mechanics
Force
Utility
Targets
Secondary muscles
Preparation
```

If the Compare page is empty, no exercises have been selected yet.

---

# Random

The **Random** tab is useful for discovery or workout inspiration.

Keyboard commands:

```text
R     Generate one random exercise
6     Generate six random exercises
```

You can optionally filter random selection by muscle.

After selecting a random result:

```text
F     Favorite
A     Add to active workout
X     Compare
```

---

# Muscles

The **Muscles** tab provides a muscle-first view of the dataset.

Workflow:

1. Select a muscle group in the left table.
2. Select an exercise in the middle table.
3. Read the full details in the right panel.

This is useful when you know what muscle you want to train but do not yet know which exercise you want.

---

# Statistics

The **Statistics** tab summarizes the exercise database.

It includes terminal-native bar charts for:

- difficulty distribution
- exercises by main muscle
- top equipment

It also displays headline values including:

```text
Total exercises
Unique exercise names
Equipment types
Muscle groups
Favorites
Average difficulty
```

The bars are rendered directly in the terminal and do not require a separate plotting window.

---

# Favorites

Highlight an exercise and press:

```text
F
```

A star indicates that the exercise is favorited.

Favorites are stored in SQLite and persist between sessions.

---

# Search

Simple search:

```text
bench press
```

The search field also supports structured filters in builds where advanced query syntax is enabled.

Examples:

```text
muscle:Chest
equipment:Dumbbell
muscle:Chest equipment:Dumbbell
muscle:Chest difficulty:3
muscle:Chest -equipment:Machine
```

You can also use the visible dropdown filters without learning query syntax.

---

# Keyboard reference

```text
Q       Quit
/       Focus search
R       One random exercise
6       Six random exercises
F       Favorite selected exercise
A       Add selected exercise to active workout
X       Select exercise for comparison
E       Export
C       Clear filters
↑/↓     Navigate tables
Tab     Move focus between controls
Enter   Activate focused buttons/controls
```

---

# CLI usage

ExerxEye can also be used without launching the TUI.

## Search

```bash
exerx-eye search "bench press"
```

## Random exercise

```bash
exerx-eye random --muscle Chest --count 1
```

Six exercises:

```bash
exerx-eye random --muscle Chest --count 6
```

## Statistics

```bash
exerx-eye stats
```

## Health check

```bash
exerx-eye doctor
```

## Export

```bash
exerx-eye export exercises.csv
```

## Launch TUI

```bash
exerx-eye tui
```

---

# Local data

ExerxEye stores its local SQLite data in the application data directory.

The branded build uses an ExerxEye-specific data location/database rather than requiring the CSV every time the TUI launches.

Use:

```bash
exerx-eye doctor
```

to check database health and record counts.

---

# API

ExerxEye also includes an optional FastAPI service for programmatic access.

Typical routes include:

```text
GET /health
GET /exercises
GET /exercises/{id}
GET /random
GET /muscles
GET /stats
```

The API is not required to use the TUI.

---

# Docker

To launch the API container:

```bash
docker compose up --build -d
```

Check containers:

```bash
docker compose ps
```

Test health:

```bash
curl http://localhost:8000/health
```

Swagger/OpenAPI documentation is available at:

```text
http://localhost:8000/docs
```

Stop the service with:

```bash
docker compose down
```

---

# Testing

Install pytest if necessary:

```bash
python -m pip install pytest
```

Then run:

```bash
python -m pytest -q
```

---

# Troubleshooting

## `exerx-eye: command not found`

Make sure the project is installed into the active environment:

```bash
source .venv/bin/activate
python -m pip install -e .
```

Check:

```bash
which exerx-eye
```

## Wrong virtual environment

Check:

```bash
which python
```

The path should point inside the current ExerxEye project:

```text
.../exerx-eye/.venv/bin/python
```

If it points to another project:

```bash
deactivate
cd ~/Downloads/exerx-eye
source .venv/bin/activate
```

## Empty exercise database

Run:

```bash
exerx-eye import data/gym_exercise_dataset.csv
```

## Import says `Imported 0 exercises`

The exercises are probably already present.

Run:

```bash
exerx-eye stats
```

or:

```bash
exerx-eye doctor
```

to verify the database count.

## Compare is empty

Go to Browse and press `X` on two exercises.

## Workout has no exercises

Select the workout first, go to Browse, highlight an exercise, and press `A`.

## Progress has no data

Create a workout, start a session, log at least one weighted set, and finish the session.

---

# Architecture

```text
Exercise Dataset
      │
      ▼
SQLite Repository
      │
      ├── Exercise Search
      ├── Favorites
      ├── Workouts
      │      └── Sessions
      │             └── Sets
      │                    └── Progress Analytics
      │
      ├── Textual TUI
      ├── CLI
      └── FastAPI REST service
```

The TUI does not require the API to be running. SQLite is the local source of truth for the terminal application.

---

# Product naming

```text
Product        ExerxEye
Tagline        Exercise Intelligence & Analytics
CLI            exerx-eye
Python package exerx_eye
```

---

# License

See the repository license for distribution and reuse terms.
